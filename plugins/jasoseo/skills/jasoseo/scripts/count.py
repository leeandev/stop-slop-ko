# -*- coding: utf-8 -*-
"""jasoseo 글자 수 계산기.

자소서 초안 본문의 글자 수를 채용 사이트에서 쓰는 여러 기준으로 센다.
초안 파일의 `#` 제목 줄과 `<!-- -->` 메모는 본문에서 뺀다.

usage: python count.py [FILE ...] [--limit N] [--basis space|nospace]
exit : 0 = 제한 안(또는 제한 없음), 1 = 제한 초과, 2 = 입력 오류
"""
import argparse
import re
import sys
from pathlib import Path

COMMENT = re.compile(r"<!--.*?-->[ \t]*\n?", re.S)
HEADING = re.compile(r"^#{1,6}\s.*(?:\n|$)", re.M)
GAP = re.compile(r"\[확인 필요[^\]]*\]")
WS = re.compile(r"\s")
LOW_PCT = 90
BASIS_LABEL = {"space": "공백 포함", "nospace": "공백 제외"}


def body(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = COMMENT.sub("", text)
    text = HEADING.sub("", text)
    return text.strip()


def euckr_bytes(text):
    total, bad = 0, []
    for ch in text:
        try:
            total += len(ch.encode("cp949"))
        except UnicodeEncodeError:
            total += 2
            bad.append(ch)
    return total, bad


def count(text):
    b = body(text)
    euckr, bad = euckr_bytes(b)
    return {
        "space": len(b),
        "space_no_newline": len(b.replace("\n", "")),
        "nospace": len(WS.sub("", b)),
        "utf8": len(b.encode("utf-8")),
        "euckr": euckr,
        "non_euckr": sorted(set(bad)),
        "gaps": len(GAP.findall(b)),
    }


def judge(n, limit):
    if n > limit:
        return "over"
    if n * 100 < limit * LOW_PCT:
        return "under"
    return "ok"


def report(name, c, limit=None, basis="space"):
    lines = [
        f"== {name}",
        f"공백 포함 {c['space']}자 (줄바꿈 제외 {c['space_no_newline']}자) | 공백 제외 {c['nospace']}자"
        f" | UTF-8 {c['utf8']}B | EUC-KR {c['euckr']}B",
    ]
    if c["non_euckr"]:
        lines.append(f"! EUC-KR에 없는 문자 {''.join(c['non_euckr'])}: 2바이트로 셈, 옛 채용 사이트에서는 깨질 수 있음")
    if c["gaps"]:
        lines.append(f"! [확인 필요] {c['gaps']}곳 남음")
    status = None
    if limit:
        n = c[basis]
        status = judge(n, limit)
        rest = limit - n
        left = f"남음 {rest}자" if rest >= 0 else f"초과 {-rest}자"
        verdict = {"ok": "범위 안", "under": f"짧음(목표 {LOW_PCT}% 이상)", "over": "초과"}[status]
        lines.append(f"{BASIS_LABEL[basis]} 제한 {limit}자 중 {n}자 ({n * 100 // limit}%), {left}: {verdict}")
    lines.append("※ 사이트마다 세는 방식이 다릅니다(줄바꿈을 2자로 세는 곳도 있음). 제출 화면의 글자 수를 마지막으로 확인하세요.")
    return "\n".join(lines), status


def read(path):
    data = Path(path).read_bytes()
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("cp949")


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="자소서 글자 수 계산")
    ap.add_argument("files", nargs="*")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--basis", choices=["space", "nospace"], default="space")
    a = ap.parse_args(argv)
    if a.limit is not None and a.limit <= 0:
        print("--limit은 1 이상이어야 합니다", file=sys.stderr)
        return 2
    sources = []
    if a.files:
        for f in a.files:
            try:
                sources.append((f, read(f)))
            except (OSError, UnicodeDecodeError) as e:
                print(f"읽을 수 없음: {f} ({e})", file=sys.stderr)
                return 2
    else:
        sources.append(("stdin", sys.stdin.buffer.read().decode("utf-8-sig", errors="replace")))
    over = False
    for name, text in sources:
        out, status = report(name, count(text), a.limit, a.basis)
        print(out)
        over = over or status == "over"
    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main())
