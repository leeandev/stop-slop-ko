# -*- coding: utf-8 -*-
"""stop-slop-ko 잔여 신호 스캐너.

docx/pptx/xlsx/md/txt/html 본문을 문단(셀) 단위로 뽑아 references/ko-slop-patterns.md의
기계 판정 가능한 신호만 찾는다. 번역투·상투구 판단은 사람(모델) 몫.

usage: python slop_scan.py FILE [FILE ...] [--info] [--prose] [--out report.txt]
exit : 0 = WARN 없음(PASS), 1 = WARN 있음(FAIL), 2 = 입력 오류
"""
import argparse
import html
import posixpath
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
S = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PR = "{http://schemas.openxmlformats.org/package/2006/relationships}"

HANGUL = re.compile(r"[가-힣]")
EMOJI = re.compile("[✅❌❎✨⭐\U0001F300-\U0001FAFF]")
PARTICLE = re.compile(r"""[A-Za-z0-9%)\]"'”’] (은|는|이|가|을|를|에|에서|에게|와|과|로|으로|의)(?=[\s,.)]|$)""")

# (code, level, regex, 설명). 붙임 복합어 middot(성능·품질)·화살표·※는 신호 아님.
RULES = [
    ("EMDASH", "WARN", re.compile(r"—"), "산문 속 em-dash: 콜론/괄호/문장 분리"),
    ("STAR", "WARN", re.compile(r"[★☆]"), "장식 별표: 삭제(강조는 볼드/색)"),
    ("EMOJI", "WARN", EMOJI, "장식 이모지: 삭제"),
    ("DIVIDE", "WARN", re.compile(r"÷"), "수식기호: 말로 풀기"),
    ("MIDDOT_SPACED2", "WARN", re.compile(r"[  ]·[  ].*[  ]·[  ]"), "공백 가운뎃점 나열: 쉼표 또는 /"),
    ("MIDDOT_DOUBLE", "WARN", re.compile(r" {2,}·|· {2,}"), "이중 공백 구분자: 단일 구분자"),
    ("PARTICLE_SPACE", "WARN", PARTICLE, "조사 앞 공백: 붙이기"),
    ("TL_ISSEO", "WARN", re.compile(r"에 있어서?(?=[\s,])"), "번역투 '~에 있어(서)': 생략 또는 '~에서'"),
    ("TL_TONGHAYEO", "WARN", re.compile(r"[을를] 통하여"), "번역투 '~을 통하여': '~로/~으로'"),
    ("TL_DOEEOJI", "WARN", re.compile(r"되어[지진져질짐집]"), "이중 피동: '~되다'"),
    ("TL_HALSUITDA", "WARN", re.compile(r"(이)?라고? 할 수 있"), "번역투 '~라 할 수 있다': 단정"),
    ("TL_DAEBI_SANGI", "INFO", re.compile(r"대비.{0,30}상이"), "번역투 '대비 … 상이': '~와 다름' 검토"),
    ("MIDDOT_SPACED1", "INFO", re.compile(r"[  ]·[  ]"), "공백 가운뎃점 1회: 2항목 속성 구분이면 유지"),
    ("RANGE_SPACE", "INFO", re.compile(r"\d[A-Za-z%]* ~ \d"), "범위 공백: 붙이면 깔끔(1K~20K)"),
    ("ENDASH", "INFO", re.compile(r" – "), "산문 속 en-dash"),
]

# --prose: 서술형 글(리포트, 에세이, 자소서, 블로그, 칼럼). 줄 단위는 INFO, 판단은 사람이.
PROSE_RULES = [
    ("PROSE_LESSON", "INFO", re.compile(r"깨달았|깨닫게\s*되|중요성을\s*(알게|배웠|배우게|느꼈|실감)|교훈을\s*(얻|배)"),
     "교훈형 마무리: 그 뒤 실제로 바뀐 행동이나 사실로"),
    ("PROSE_NOTJUST", "INFO", re.compile(r"(?<![가-힣])(단순(한|히)?|그저|단지)\s[^.!?\n]{0,30}?아(닌|니라|니었)|에\s*그치지\s*않"),
     "'단순한 ~이 아닌'·'~에 그치지 않고' 대비 틀: 사실만 남기기"),
    ("PROSE_EMPTY_EMPH", "INFO", re.compile(r"(?<![가-힣])(정말|매우|굉장히|진정한|진정으로|무엇보다)(?=\s)"),
     "빈 강조어: 지우거나 숫자·사실로"),
    ("PROSE_CLICHE_REPORT", "INFO",
     re.compile(r"본\s*(보고서|리포트|레포트|글)에서는|알아보고자\s*한다|이상으로\s*[^.\n]{0,20}살펴보았|시사하는\s*바가\s*(크|많)"),
     "리포트 상투구: 바로 주장·사실로 시작/끝"),
    ("PROSE_CLICHE_BLOG", "INFO",
     re.compile(r"오늘은\s[^.\n]{0,30}알아보(겠|도록|려고)|도움이\s*되(셨|었)(길|으면)|시작해\s*볼까요|꿀팁"),
     "블로그 상투구: 인사 대신 본론"),
]
QUOTE_OPEN = re.compile(r"^\s*(>\s*)?[“\"「『‘']|사전적\s*(의미|정의)|사전에\s*(따르면|서는)|(이)?라는\s*말(이\s*있|처럼)")
# "~라고 본다면"처럼 조건절로 이어지면 의견 종결이 아니다.
THINK = re.compile(r"([다라]고\s*(생각(한다|합니다|했다|했습니다|해요|된다|됩니다)|본다|봅니다)|"
                   r"[다라]는\s*생각이\s*(든다|듭니다|들었다|들었습니다))(?!면)")
CONNECTOR = re.compile(r"^\s*(또한|나아가|더불어|결론적으로|이처럼|이를\s*통해|따라서|그러므로|뿐만\s*아니라)[,\s]")
THINK_MIN, THINK_PER_CHARS = 3, 1000
CONNECTOR_MIN, CONNECTOR_RATIO = 3, 0.25


def is_heading(text):
    return text.lstrip().startswith("#")


LIST_ITEM = re.compile(r"^\s*([-*+]|\d+[.)])\s")


def front_matter_end(path):
    """md 머리말(--- ... ---)의 마지막 줄 번호. 없으면 0."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return 0
    for n, line in enumerate(lines[1:], 2):
        if line.strip() == "---":
            return n
    return 0


def split_paragraphs(paras, group_lines=False, skip_until=0):
    """판정용 문단 목록. 셀 안의 빈 줄은 문단을 나누고, md는 빈 줄 없이 이어진 줄을 한 문단으로 묶는다.
    제목 줄과 목록 항목은 따로 세고, 표 셀과 머리말(skip_until 줄까지)은 문단으로 세지 않는다."""
    out, prev_n = [], None
    for where, text in paras:
        if where.endswith("(표)"):
            prev_n = None
            continue
        line_no = re.match(r"L(\d+)", where)
        if line_no and int(line_no.group(1)) <= skip_until:
            continue
        m = re.fullmatch(r"L(\d+)", where) if group_lines else None
        n = int(m.group(1)) if m else None
        alone = is_heading(text) or LIST_ITEM.match(text)
        if (n is not None and prev_n is not None and n == prev_n + 1 and not alone and out
                and not is_heading(out[-1][1]) and not LIST_ITEM.match(out[-1][1])):
            out[-1] = (out[-1][0], out[-1][1] + " " + text.strip())
        else:
            out.extend((where, part) for part in re.split(r"\n\s*\n", text) if HANGUL.search(part))
        prev_n = n
    return out


def prose_totals(paras, show_info):
    """문서 전체 기준 서술형 신호. paras = [(where, text)] (한글 있는 본문 문단)."""
    hits = []
    body = [(w, t) for w, t in paras if not is_heading(t)]
    if not body:
        return hits
    first_w, first_t = body[0]
    if show_info and QUOTE_OPEN.search(first_t):
        hits.append(("INFO", "PROSE_QUOTE_OPEN", first_w, first_t.strip()[:50], "명언·사전 정의로 시작: 장면이나 사실로"))
    chars = sum(len(t) for _w, t in body)
    think = sum(len(THINK.findall(t)) for _w, t in body)
    if think >= THINK_MIN and think * THINK_PER_CHARS >= chars:
        rate = think * THINK_PER_CHARS / chars
        hits.append(("WARN", "PROSE_THINK", "(문서 전체)", f"'~라고 생각한다' {think}회 / 1,000자당 {rate:.1f}회 ({chars}자)",
                     "사실·행동으로 말하거나 단정"))
    conn = sum(1 for _w, t in body if CONNECTOR.search(t))
    if conn >= CONNECTOR_MIN and conn >= CONNECTOR_RATIO * len(body):
        hits.append(("WARN", "PROSE_CONNECTOR", "(문서 전체)", f"연결어로 시작하는 문단 {len(body)}개 중 {conn}개",
                     "꼭 필요한 곳 하나만 남기기"))
    return hits


def is_marker(text):
    """표의 해당없음 마커(—, -, ―)만 있는 셀."""
    return text.strip() in {"—", "-", "―", "–", "N/A"}


def parent_map(root):
    return {c: p for p in root.iter() for c in p}


def paragraphs_xml(root, p_tag, t_tag):
    """t 요소를 가장 가까운 p 조상에 모은다(텍스트박스 중첩 문단도 분리)."""
    parents = parent_map(root)
    order, buf = [], {}
    for p in root.iter(p_tag):
        order.append(p)
        buf[p] = []
    for t in root.iter(t_tag):
        node = parents.get(t)
        while node is not None and node.tag != p_tag:
            node = parents.get(node)
        if node is not None and t.text:
            buf[node].append(t.text)
    return [(i, "".join(buf[p]), p, parents) for i, p in enumerate(order, 1)]


def has_ancestor(node, parents, tag):
    node = parents.get(node)
    while node is not None:
        if node.tag == tag:
            return True
        node = parents.get(node)
    return False


def rels(z, path):
    base = posixpath.dirname(path)
    rp = posixpath.join(base, "_rels", posixpath.basename(path) + ".rels")
    if rp not in z.namelist():
        return {}
    out = {}
    for r in ET.fromstring(z.read(rp)).iter(PR + "Relationship"):
        tgt = r.get("Target")
        out[r.get("Id")] = tgt.lstrip("/") if tgt.startswith("/") else posixpath.normpath(posixpath.join(base, tgt))
    return out


def extract_docx(path):
    with zipfile.ZipFile(path) as z:
        parts = ["word/document.xml"] + sorted(
            n for n in z.namelist() if re.match(r"word/(header|footer|footnotes|endnotes)\d*\.xml$", n))
        for part in parts:
            if part not in z.namelist():
                continue
            root = ET.fromstring(z.read(part))
            label = "본문" if part == "word/document.xml" else Path(part).stem
            for i, text, p, parents in paragraphs_xml(root, W + "p", W + "t"):
                where = f"{label} p{i}" + (" (표)" if has_ancestor(p, parents, W + "tc") else "")
                yield where, text


def extract_pptx(path):
    with zipfile.ZipFile(path) as z:
        prs = ET.fromstring(z.read("ppt/presentation.xml"))
        rmap = rels(z, "ppt/presentation.xml")
        slides = [rmap[s.get(R + "id")] for s in prs.iter(
            "{http://schemas.openxmlformats.org/presentationml/2006/main}sldId")]
        for n, part in enumerate(slides, 1):
            root = ET.fromstring(z.read(part))
            for i, text, p, parents in paragraphs_xml(root, A + "p", A + "t"):
                where = f"slide{n} p{i}" + (" (표)" if has_ancestor(p, parents, A + "tc") else "")
                yield where, text


def extract_xlsx(path):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        shared = []
        if "xl/sharedStrings.xml" in names:
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(S + "si"):
                phonetic = {t for rph in si.iter(S + "rPh") for t in rph.iter(S + "t")}
                shared.append("".join(t.text or "" for t in si.iter(S + "t") if t not in phonetic))
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rmap = rels(z, "xl/workbook.xml")
        for sh in wb.iter(S + "sheet"):
            part = rmap.get(sh.get(R + "id"))
            if not part or part not in names:
                continue
            name = sh.get("name")
            for c in ET.fromstring(z.read(part)).iter(S + "c"):
                t, v = c.get("t"), c.find(S + "v")
                if t == "s" and v is not None:
                    text = shared[int(v.text)]
                elif t == "inlineStr":
                    text = "".join(x.text or "" for x in c.iter(S + "t"))
                elif t == "str" and v is not None:
                    text = v.text or ""
                else:
                    continue
                yield f"{name}!{c.get('r')}", text
        for part in sorted(n for n in names if re.match(r"xl/drawings/drawing\d+\.xml$", n)):
            root = ET.fromstring(z.read(part))
            for i, text, _p, _par in paragraphs_xml(root, A + "p", A + "t"):
                yield f"{Path(part).stem}(도형) p{i}", text


def extract_md(path):
    fence = False
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if line.lstrip().startswith(("```", "~~~")):
            fence = not fence
            continue
        if fence:
            continue
        # 인라인 코드는 자리표시자로: 지우면 "kit `a.zip`은"이 "kit 은"이 되어 조사 공백 오탐
        line = re.sub(r"`[^`]*`", "X", line)
        if line.strip().startswith("|"):
            for k, cell in enumerate(line.strip().strip("|").split("|"), 1):
                if not re.fullmatch(r"\s*:?-{2,}:?\s*", cell):
                    yield f"L{n} c{k} (표)", cell.strip()
        else:
            yield f"L{n}", line


def extract_html(path):
    src = Path(path).read_text(encoding="utf-8")
    src = re.sub(r"(?is)<(script|style|pre|code)\b.*?</\1>", " ", src)
    src = re.sub(r"(?i)<(br|/p|/div|/li|/h\d|/td|/th|/tr)\b[^>]*>", "\n", src)
    for n, line in enumerate(html.unescape(re.sub(r"<[^>]+>", "", src)).splitlines(), 1):
        if line.strip():
            yield f"L{n}", line


EXTRACTORS = {".docx": extract_docx, ".pptx": extract_pptx, ".xlsx": extract_xlsx, ".xlsm": extract_xlsx,
              ".md": extract_md, ".txt": extract_md, ".html": extract_html, ".htm": extract_html}


def scan(path, show_info, prose=False):
    hits, quotes, paras = [], {"curly": 0, "straight": 0}, []
    rules = RULES + PROSE_RULES if prose else RULES
    for where, text in EXTRACTORS[path.suffix.lower()](path):
        if not text.strip() or is_marker(text):
            continue
        # 한글 없는 순수 영문/코드 셀은 대상 아님
        if not HANGUL.search(text):
            continue
        paras.append((where, text))
        quotes["curly"] += len(re.findall(r"[“”]", text))
        quotes["straight"] += text.count('"')
        seen_middot2 = False
        for code, level, rx, hint in rules:
            if code == "MIDDOT_SPACED1" and seen_middot2:
                continue
            m = rx.search(text)
            if not m:
                continue
            if code == "MIDDOT_SPACED2":
                seen_middot2 = True
            if level == "INFO" and not show_info:
                continue
            s, e = max(0, m.start() - 25), min(len(text), m.end() + 25)
            snippet = ("…" if s else "") + text[s:e].replace("\n", " ") + ("…" if e < len(text) else "")
            hits.append((level, code, where, snippet, hint))
    if quotes["curly"] and quotes["straight"] and show_info:
        hits.append(("INFO", "QUOTE_MIX", "(문서 전체)",
                     f"곡선 {quotes['curly']} / 곧은 {quotes['straight']}", "문서 기존 관례로 통일"))
    if prose:
        # txt는 줄바꿈 하나로 문단을 나누는 글(웹 폼·HWP에서 복사)이 많아 묶지 않는다
        is_md = path.suffix.lower() == ".md"
        skip = front_matter_end(path) if is_md else 0
        hits.extend(prose_totals(split_paragraphs(paras, is_md, skip), show_info))
    return hits


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--info", action="store_true", help="INFO(판단 필요) 항목도 표시")
    ap.add_argument("--prose", action="store_true", help="서술형 글(리포트·에세이·블로그) 규칙도 검사")
    ap.add_argument("--out", help="리포트를 UTF-8 파일로 저장(콘솔 cp949 회피)")
    args = ap.parse_args()

    lines, total_warn, bad_input = [], 0, False
    for f in args.files:
        path = Path(f)
        if path.name.startswith("~$"):
            continue
        if not path.is_file() or path.suffix.lower() not in EXTRACTORS:
            lines.append(f"[SKIP] {f}: 파일 없음 또는 미지원 확장자")
            bad_input = True
            continue
        try:
            hits = scan(path, args.info, args.prose)
        except (zipfile.BadZipFile, ET.ParseError, KeyError, UnicodeDecodeError) as e:
            lines.append(f"[ERROR] {f}: {type(e).__name__}: {e}")
            bad_input = True
            continue
        warn = sum(1 for h in hits if h[0] == "WARN")
        total_warn += warn
        lines.append(f"== {path.name}: WARN {warn}, INFO {len(hits) - warn}")
        for level, code, where, snippet, hint in hits:
            lines.append(f"  [{level}] {code} @ {where}: {snippet}\n         -> {hint}")
    lines.append(f"RESULT: {'FAIL' if total_warn else 'PASS'} (WARN {total_warn})")

    report = "\n".join(lines)
    if args.out:
        Path(args.out).write_text(report + "\n", encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(report)
    sys.exit(2 if bad_input and not total_warn else (1 if total_warn else 0))


if __name__ == "__main__":
    main()
