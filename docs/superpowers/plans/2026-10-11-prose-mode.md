# stop-slop-ko 서술형 문체 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** stop-slop-ko가 리포트·에세이·자소서·블로그·칼럼 같은 서술형 글도 생성·정제·톤 맞춤하고, 스캐너 `--prose`와 훅이 이를 돕게 한다.

**Architecture:** 모드는 그대로 두고 레지스터 결정에 서술형을 더한다. 서술형 규칙은 `references/prose-patterns.md` 한 파일, 기계 판정은 `slop_scan.py --prose`(줄 단위 INFO + 문서 전체 WARN), 훅은 서술형 키워드와 jasoseo 설치 확인을 더한다.

**Tech Stack:** Python 3 표준 라이브러리, unittest, Claude Code 플러그인(SKILL.md, UserPromptSubmit 훅)

**Spec:** `docs/superpowers/specs/2026-10-11-prose-mode-design.md`

## Global Constraints

- 표준 라이브러리만 쓴다(스캐너·훅 모두).
- `--prose` 없이 돌린 스캔 결과와 exit 코드(0 PASS, 1 WARN, 2 입력 오류)는 지금과 같아야 한다.
- 정제 모드는 종결어미를 바꾸지 않는다(서술형 포함).
- "보고서"는 개조식 그대로. 서술형은 리포트·레포트·과제 같은 말이나 문단 글 요청에서만.
- 생성 기본 종결: 리포트·에세이·칼럼·기고문·일반 블로그 `~다`, 자소서·안내형 블로그 `~습니다`.
- 문서 전체 WARN: PROSE_THINK = 3회 이상 AND 공백 포함 1,000자당 1회 이상, PROSE_CONNECTOR = 연결어 시작 문단 3개 이상 AND 전체 문단의 25% 이상. 메시지에 실제 값을 낸다.
- jasoseo 확인(`installed_plugins.json`, `settings.json` `enabledPlugins`) 실패 시 미설치로 본다.
- README·스킬에 AI 검사기 회피 문구를 쓰지 않는다.
- 버전: stop-slop-ko 플러그인과 marketplace metadata 1.1.0 → 1.2.0.

## Review Focus

1. md 제목 줄(`# ...`)과 목록 기호 줄이 연결어 문단 비율의 분모를 부풀리거나 연결어로 오판되는 경우 → 제목 줄은 문단 수에서 뺀다(Task 1 테스트).
2. 짧은 글(800자)에서 "생각한다" 2회 → PASS, 3회 → WARN. 긴 글(6,000자)에서 3회 → PASS(Task 1 테스트).
3. "과제 보고서 써줘"처럼 서술형 키워드와 개조식 문서 키워드가 같이 오는 요청 → 개조식(slop) 판정(Task 2 selftest).
4. `installed_plugins.json`이 깨졌거나 없음 → 미설치로 보고 자소서 요청에 prose 메시지(Task 2 테스트).
5. 서술형 글의 정제에서 `~습니다`가 `~다`로 바뀌는 회귀 → 시나리오 1 통과 기준(Task 4).

---

### Task 1: 스캐너 `--prose`

**Files:**
- Modify: `plugins/stop-slop-ko/skills/stop-slop-ko/scripts/slop_scan.py`
- Test: `tests/test_slop_scan.py` (신설)

**Interfaces:**
- Produces: `scan(path, show_info, prose=False) -> list[tuple(level, code, where, snippet, hint)]`, `prose_totals(paras, show_info) -> list[hit]` (`paras`는 `[(where, text)]`), 상수 `THINK_MIN=3`, `THINK_PER_CHARS=1000`, `CONNECTOR_MIN=3`, `CONNECTOR_RATIO=0.25`, CLI `--prose`.

- [ ] **Step 1: 실패하는 테스트 작성** `tests/test_slop_scan.py`

```python
# -*- coding: utf-8 -*-
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "plugins" / "stop-slop-ko" / "skills" / "stop-slop-ko" / "scripts" / "slop_scan.py"
sys.path.insert(0, str(SCRIPT.parent))

import slop_scan as S  # noqa: E402

FILLER = "회사는 작년부터 재택근무를 시범 운영했고 올해 전 부서로 넓혔다."  # 35자


def body(n_chars):
    """n_chars 안팎의 평범한 문단들."""
    paras, total = [], 0
    while total < n_chars:
        paras.append(FILLER)
        total += len(FILLER)
    return paras


class Base(unittest.TestCase):
    def md(self, lines):
        d = tempfile.mkdtemp()
        p = Path(d) / "t.md"
        p.write_text("\n\n".join(lines), encoding="utf-8")
        return p

    def codes(self, lines, prose=True, info=True):
        return [h[1] for h in S.scan(self.md(lines), info, prose)]


class NoProseUnchanged(Base):
    def test_prose_rules_off_by_default(self):
        lines = ["본 보고서에서는 재택근무를 알아보고자 한다.", "협업의 중요성을 깨달았다."]
        self.assertFalse([c for c in self.codes(lines, prose=False) if c.startswith("PROSE")])

    def test_existing_rules_still_fire_with_prose(self):
        self.assertIn("EMDASH", self.codes(["재택근무 — 장점이 많다."]))


class LineInfo(Base):
    def test_lesson(self):
        self.assertIn("PROSE_LESSON", self.codes(["이 일로 협업의 중요성을 깨달았다."]))

    def test_notjust(self):
        self.assertIn("PROSE_NOTJUST", self.codes(["단순한 과제가 아닌 도전이었다."]))

    def test_empty_emph(self):
        self.assertIn("PROSE_EMPTY_EMPH", self.codes(["정말 많은 것을 배웠다."]))

    def test_report_cliche(self):
        self.assertIn("PROSE_CLICHE_REPORT", self.codes(["본 보고서에서는 재택근무를 알아보고자 한다."]))

    def test_blog_cliche(self):
        self.assertIn("PROSE_CLICHE_BLOG", self.codes(["오늘은 Docker 볼륨에 대해 알아보겠습니다."]))

    def test_quote_open_first_paragraph_only(self):
        self.assertIn("PROSE_QUOTE_OPEN", self.codes(["# 제목", "“실패는 성공의 어머니”라는 말이 있다.", FILLER]))
        self.assertNotIn("PROSE_QUOTE_OPEN", self.codes([FILLER, "“실패는 성공의 어머니”라는 말이 있다."]))

    def test_info_hidden_without_flag(self):
        self.assertFalse(self.codes(["협업의 중요성을 깨달았다."], info=False))


class ThinkWarn(Base):
    T = "나는 이 방식이 맞다고 생각한다."

    def test_short_two_pass(self):
        self.assertNotIn("PROSE_THINK", self.codes(body(700) + [self.T] * 2))

    def test_short_three_warn(self):
        hits = S.scan(self.md(body(700) + [self.T] * 3), False, True)
        warn = [h for h in hits if h[1] == "PROSE_THINK"]
        self.assertEqual(warn[0][0], "WARN")
        self.assertIn("3회", warn[0][3])

    def test_long_three_pass(self):
        self.assertNotIn("PROSE_THINK", self.codes(body(6000) + [self.T] * 3))

    def test_long_dense_warn(self):
        self.assertIn("PROSE_THINK", self.codes(body(6000) + [self.T] * 7))


class ConnectorWarn(Base):
    C = "또한 재택근무는 통근 시간을 줄였다."

    def test_three_of_six_warn(self):
        self.assertIn("PROSE_CONNECTOR", self.codes([FILLER] * 3 + [self.C] * 3))

    def test_three_of_twenty_pass(self):
        self.assertNotIn("PROSE_CONNECTOR", self.codes([FILLER] * 17 + [self.C] * 3))

    def test_two_pass(self):
        self.assertNotIn("PROSE_CONNECTOR", self.codes([FILLER] * 2 + [self.C] * 2))

    def test_headings_not_counted(self):
        # 문단 9개 중 3개(33%) → WARN. 제목 줄 4개가 분모에 들어가면 23%로 PASS가 되어 버린다
        lines = ["# 1장", "# 2장", "# 3장", "# 4장"] + [FILLER] * 6 + [self.C] * 3
        self.assertIn("PROSE_CONNECTOR", self.codes(lines))


class Cli(Base):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True)

    def test_exit_codes(self):
        p = self.md(body(700) + ["맞다고 생각한다."] * 3)
        self.assertEqual(self.run_cli(str(p)).returncode, 0)
        self.assertEqual(self.run_cli(str(p), "--prose").returncode, 1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 실패 확인** — `python -m unittest tests.test_slop_scan -v` → `scan()`이 세 번째 인자를 받지 않아 TypeError.

- [ ] **Step 3: 구현** `slop_scan.py`

RULES 아래에 추가:

```python
# --prose: 서술형 글(리포트, 에세이, 자소서, 블로그, 칼럼). 줄 단위는 INFO, 판단은 사람이.
PROSE_RULES = [
    ("PROSE_LESSON", "INFO", re.compile(r"깨달았|깨닫게\s*되|중요성을\s*(알게|배웠|배우게|느꼈|실감)|교훈을\s*(얻|배)"),
     "교훈형 마무리: 그 뒤 실제로 바뀐 행동이나 사실로"),
    ("PROSE_NOTJUST", "INFO", re.compile(r"단순(한|히)\s[^.!?\n]{0,30}?아(닌|니라|니었)"),
     "'단순한 ~이 아닌' 대비 틀: 사실만 남기기"),
    ("PROSE_EMPTY_EMPH", "INFO", re.compile(r"(?<![가-힣])(정말|매우|굉장히|진정한|진정으로|무엇보다)(?=\s)"),
     "빈 강조어: 지우거나 숫자·사실로"),
    ("PROSE_CLICHE_REPORT", "INFO",
     re.compile(r"본\s*(보고서|리포트|레포트|글)에서는|알아보고자\s*한다|이상으로\s*[^.\n]{0,20}살펴보았|시사하는\s*바가\s*(크|많)"),
     "리포트 상투구: 바로 주장·사실로 시작/끝"),
    ("PROSE_CLICHE_BLOG", "INFO",
     re.compile(r"오늘은\s[^.\n]{0,30}알아보(겠|도록|려고)|도움이\s*되(셨|었)(길|으면)|시작해\s*볼까요|꿀팁"),
     "블로그 상투구: 인사 대신 본론"),
]
QUOTE_OPEN = re.compile(r"^\s*[“\"「『‘']|사전적\s*(의미|정의)|사전에\s*(따르면|서는)|(이)?라는\s*말(이\s*있|처럼)")
THINK = re.compile(r"[다라]고\s*생각(한다|합니다|했다|했습니다|해요)")
CONNECTOR = re.compile(r"^\s*(또한|나아가|더불어|결론적으로|이처럼|이를\s*통해|따라서|그러므로|뿐만\s*아니라)[,\s]")
THINK_MIN, THINK_PER_CHARS = 3, 1000
CONNECTOR_MIN, CONNECTOR_RATIO = 3, 0.25


def is_heading(text):
    return text.lstrip().startswith("#")


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
```

`scan()` 바꾸기: 시그니처 `def scan(path, show_info, prose=False):`, 루프 앞 `rules = RULES + PROSE_RULES if prose else RULES` 와 `paras = []`, 한글 검사 뒤 `paras.append((where, text))`, `for code, level, rx, hint in rules:`, return 앞에 `if prose: hits.extend(prose_totals(paras, show_info))`. 줄 단위 PROSE 규칙은 제목 줄에도 돈다(제목 상투구도 신호).

`main()`: `ap.add_argument("--prose", action="store_true", help="서술형 글(리포트·에세이·블로그) 규칙도 검사")`, `scan(path, args.info, args.prose)`. docstring usage 줄에 `[--prose]` 추가.

- [ ] **Step 4: 통과 확인** — `python -m unittest tests.test_slop_scan -v` 전부 PASS, `python -m unittest discover tests` 전부 PASS.

- [ ] **Step 5: 커밋** — `git add tests/test_slop_scan.py plugins/stop-slop-ko/skills/stop-slop-ko/scripts/slop_scan.py` / `git commit -m "feat(stop-slop-ko): slop_scan --prose 서술형 신호"`

### Task 2: 훅 서술형 키워드와 jasoseo 설치 확인

**Files:**
- Modify: `plugins/stop-slop-ko/hooks/stop-slop-doc-reminder.py`
- Test: `tests/test_hook.py` (신설), 훅 `--selftest`

**Interfaces:**
- Consumes: Task 1의 CLI `--prose`(메시지 안내문)
- Produces: `jasoseo_active(home=None) -> bool`, `route(prompt, jasoseo=None) -> (kind, kw) | None`, 새 kind `"prose"`

- [ ] **Step 1: 실패하는 테스트** `tests/test_hook.py`

```python
# -*- coding: utf-8 -*-
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "plugins" / "stop-slop-ko" / "hooks" / "stop-slop-doc-reminder.py"
sys.path.insert(0, str(HOOK.parent))
H = __import__("stop-slop-doc-reminder")


def home(installed=None, settings=None):
    d = Path(tempfile.mkdtemp())
    if installed is not None:
        (d / "plugins").mkdir()
        (d / "plugins" / "installed_plugins.json").write_text(installed, encoding="utf-8")
    if settings is not None:
        (d / "settings.json").write_text(settings, encoding="utf-8")
    return d


INSTALLED = json.dumps({"version": 2, "plugins": {"jasoseo@stop-slop-ko": [{"scope": "user"}]}})


class JasoseoActive(unittest.TestCase):
    def test_installed_enabled(self):
        self.assertTrue(H.jasoseo_active(home(INSTALLED, json.dumps({"enabledPlugins": {"jasoseo@stop-slop-ko": True}}))))

    def test_installed_no_settings(self):
        self.assertTrue(H.jasoseo_active(home(INSTALLED)))

    def test_disabled(self):
        self.assertFalse(H.jasoseo_active(home(INSTALLED, json.dumps({"enabledPlugins": {"jasoseo@stop-slop-ko": False}}))))

    def test_not_installed(self):
        self.assertFalse(H.jasoseo_active(home(json.dumps({"version": 2, "plugins": {}}))))

    def test_missing_or_broken(self):
        self.assertFalse(H.jasoseo_active(home()))
        self.assertFalse(H.jasoseo_active(home("{broken")))


class Route(unittest.TestCase):
    def kind(self, prompt, jasoseo=True):
        r = H.route(prompt, jasoseo=jasoseo)
        return r[0] if r else None

    def test_prose(self):
        self.assertEqual(self.kind("리포트 초안 써줘"), "prose")
        self.assertEqual(self.kind("블로그 글 다듬어줘"), "prose")

    def test_report_stays_gaejo(self):
        self.assertEqual(self.kind("과제 보고서 써줘"), "slop")

    def test_jasoseo_two_states(self):
        self.assertIsNone(self.kind("자소서 초안 써줘", jasoseo=True))
        self.assertEqual(self.kind("자소서 초안 써줘", jasoseo=False), "prose")
        self.assertIsNone(self.kind("/jasoseo A사 2번", jasoseo=False))

    def test_selftest_passes(self):
        r = subprocess.run([sys.executable, str(HOOK), "--selftest"], capture_output=True)
        self.assertEqual(r.returncode, 0, r.stdout.decode("utf-8", "replace"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 실패 확인** — `python -m unittest tests.test_hook -v` → `jasoseo_active` 없음.

- [ ] **Step 3: 구현**

`import os` 추가. 정규식:

```python
# 서술형 글. 개조식 문서 키워드(FORMAL)가 같이 오면 개조식이 이긴다("과제 보고서").
PROSE = re.compile(r"리포트|레포트|에세이|과제|소논문|독후감|감상문|블로그\s*(글|포스트|포스팅)|칼럼|기고문?")
FORMAL = re.compile(r"회의록|보고서|주간보고|제안서|기획서|계획서|설계서|정의서|결과서|명세서|매뉴얼|안내문|공문|"
                    r"장표|슬라이드|\bppt|pptx|파워포인트|엑셀|xlsx|스프레드시트", re.I)
JASOSEO_ID = "jasoseo@stop-slop-ko"
```

JASOSEO 주석을 "자소서는 jasoseo가 설치·활성화돼 있으면 그쪽 몫. 없으면 서술형 글로 본다."로 바꾼다.

```python
def jasoseo_active(home=None):
    """jasoseo 플러그인이 설치되고 꺼지지 않았는지. 확인 실패는 미설치로 본다."""
    home = Path(home) if home else Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    try:
        data = json.loads((home / "plugins" / "installed_plugins.json").read_text(encoding="utf-8"))
        if not data.get("plugins", {}).get(JASOSEO_ID):
            return False
    except Exception:
        return False
    try:
        settings = json.loads((home / "settings.json").read_text(encoding="utf-8"))
        if settings.get("enabledPlugins", {}).get(JASOSEO_ID) is False:
            return False
    except Exception:
        pass
    return True
```

MESSAGES에 추가(`SCAN_PROSE = f"`\"{PYTHON}\" \"{SCANNER}\" --prose <파일>`"`):

```python
    "prose": (
        "[stop-slop-ko 자동 적용] 한국어 서술형 글(리포트, 에세이, 자소서, 블로그, 칼럼) 작성/수정 요청으로 판정됨(키워드: {kw}). "
        "stop-slop-ko 스킬을 로드해 레지스터를 서술형으로 정하고 references/prose-patterns.md를 따른다"
        "(새로 쓰기=생성, 다듬기=정제는 종결어미 불변, 다른 글 문체에 맞추기=톤 맞춤). 사실·주장·출처는 지어내지 않는다. "
        f"파일을 만들면 {SCAN_PROSE}로 검증해 결과(PASS/FAIL)를 보고할 것. 글을 쓰지 않는 요청이면 무시."
    ),
```

`route`:

```python
def route(prompt, jasoseo=None):
    """(경로, 키워드) 또는 None. jasoseo=None이면 설치 여부를 직접 확인한다."""
    head = prompt.lstrip()
    if head.startswith("/stop-slop-ko") or head.startswith("/jasoseo") or OPT_OUT.search(prompt):
        return None
    jas = JASOSEO.search(prompt)
    if jas and (jasoseo if jasoseo is not None else jasoseo_active()):
        return None
    if head.startswith("/stakeholder-brief"):
        return "brief_explicit", "/stakeholder-brief"
    verb = VERB.search(prompt)
    aud = AUDIENCE.search(prompt)
    if verb and aud:
        return "brief", aud.group(0)
    tone = TONE.search(prompt)
    prose = jas or PROSE.search(prompt)
    if prose and (verb or tone) and not FORMAL.search(prompt):
        return "prose", prose.group(0)
    if tone:
        return "slop", tone.group(0)
    doc = DOC.search(prompt)
    if verb and doc:
        return "slop", doc.group(0)
    return None
```

SELFTEST: 기존 항목은 `jasoseo=True` 상태로 판정(지금과 같음). 3번째 원소로 상태를 줄 수 있게 바꾸고 아래를 추가:

```python
    ("리포트 초안 써줘", "prose"),
    ("에세이 다듬어줘", "prose"),
    ("블로그 글 AI 티 빼줘", "prose"),
    ("칼럼 써줘", "prose"),
    ("과제 보고서 써줘", "slop"),
    ("리포트 읽고 요약만 해줘", None),
    ("자소서 초안 써줘", "prose", False),
    ("자기소개서 1번 다듬어줘", "prose", False),
```

`selftest()` 루프: `for prompt, want, *state in SELFTEST:` / `got = route(prompt, jasoseo=state[0] if state else True)`, 출력에 `(jasoseo 없음)` 표시.

"리포트 읽고 요약만 해줘"는 VERB(정리, 요약 아님)에 안 걸려 None이어야 한다. 실패하면 VERB를 고치지 말고 기대값을 확인한다.

- [ ] **Step 4: 통과 확인** — `python -m unittest tests.test_hook -v`, `python plugins/stop-slop-ko/hooks/stop-slop-doc-reminder.py --selftest` → `RESULT: PASS`.

- [ ] **Step 5: 커밋** — `feat(stop-slop-ko): 훅 서술형 키워드, jasoseo 설치 확인`

### Task 3: 스킬 문서(SKILL.md, prose-patterns.md, tone-extraction.md)

**Files:**
- Create: `plugins/stop-slop-ko/skills/stop-slop-ko/references/prose-patterns.md`
- Modify: `plugins/stop-slop-ko/skills/stop-slop-ko/SKILL.md`, `references/tone-extraction.md`

- [ ] **Step 1: prose-patterns.md 작성** — 절: 언제 읽나, 종결(기본값 표, 정제 불변), 공통 패턴 8개(신호 → 왜 AI 티 → 조치 → 전후 예시: 교훈형 마무리, "단순한 ~이 아닌", 명언·사전 정의 시작, 빈 강조어, "~라고 생각한다" 반복, 연결어 시작 문단 연속, 형용사 셋 나열·세 항목 리듬, 거창한 포부·일반론 결말), 글 종류별 상투구(리포트·과제, 블로그, 칼럼·기고문), 지어내지 않기(사실·출처·수치), 스캐너 `--prose` 코드 대응표, 판단 기준(고친 글이 같은 사람이 쓴 것처럼 읽히나).
- [ ] **Step 2: SKILL.md** — description에 서술형 트리거(리포트, 에세이, 블로그 글, 칼럼, 자소서 다듬기, "리포트 써줘", "블로그 글 다듬어줘") 추가. 첫 줄 소개에 서술형 글 포함. "언제 쓰나"에 서술형 줄 추가. 생성 1단계에 서술형 분기(Global Constraints의 기본 종결, "보고서"는 개조식, 서술형이면 prose-patterns.md 읽기). 정제 1단계 옆에 "서술형이면 prose-patterns.md, `--prose` 스캔, 종결 불변". 톤 맞춤 2단계에 "서술형 기준 글이면 tone-extraction.md 서술형 항목도". 검증 절에 `--prose` 설명(줄 단위 INFO 5종 + 첫 문단 인용, 문서 전체 WARN 2종과 기준). 자소서 줄: jasoseo가 있으면 jasoseo, 없으면 문체 패스만(인터뷰 안 함). 안 쓰는 경우의 "사실·내용 재작성"은 유지.
- [ ] **Step 3: tone-extraction.md** — 6축 표 아래에 "서술형 기준 글이면 더 보는 축": 문단 길이(문장 수), 문장 길이, 1인칭(나/저/필자/생략), 연결어 빈도.
- [ ] **Step 4: 확인** — `python plugins/stop-slop-ko/skills/stop-slop-ko/scripts/slop_scan.py plugins/stop-slop-ko/skills/stop-slop-ko/references/prose-patterns.md` 결과 확인(예시 "전" 문장의 신호는 의도된 것이므로 PASS가 아니어도 된다. 설명문 자체에 em-dash 등이 없는지만 본다).
- [ ] **Step 5: 커밋** — `feat(stop-slop-ko): 서술형 레지스터와 prose-patterns`

### Task 4: 시나리오 테스트

**Files:**
- Create: `tests/scenarios/prose.md`

- [ ] **Step 1: 시나리오 작성** — jasoseo.md 형식(발화, 준비, 통과 기준, 결과 기록 표).
  1. 블로그 글 정제: 준비 파일 `blog.md`(`~습니다`체, "오늘은 ~ 알아보겠습니다", "정말", "도움이 되셨길 바랍니다", 사실 문장 4개). 발화 "blog.md AI 티 빼줘". 통과: 종결 `~습니다` 그대로, 블로그 상투구 제거, 사실 문장·숫자 보존, `--prose` 스캔 실행·결과 보고.
  2. 리포트 정제: 준비 `report.md`(`~다`체 1,200자 안팎, "~라고 생각한다" 4회, "또한/나아가" 시작 문단 3개, 교훈형 결말). 발화 "report.md 다듬어줘". 통과: 종결 `~다` 유지, PROSE_THINK·PROSE_CONNECTOR WARN 해소, 원문에 없는 사실·출처 추가 없음, 스캔 결과 보고.
- [ ] **Step 2: 실행** — 시나리오마다 sonnet 서브에이전트에 SKILL.md·references 경로와 임시 폴더를 주고 발화를 넣는다. 결과를 표에 기록. FAIL이면 스킬 문서를 고치고 재실행.
- [ ] **Step 3: 커밋** — `test(stop-slop-ko): 서술형 시나리오와 결과`

### Task 5: 버전, README, 허브 표

**Files:**
- Modify: `plugins/stop-slop-ko/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `README.md`, `D:\dev\code\CLAUDE.md`(저장소 밖, 커밋 없음), `.gitignore`

- [ ] **Step 1** — plugin.json: description "한국어 실무문서(…)와 서술형 글(리포트, 에세이, 블로그)에서 AI 티를 걷어내는 스킬과 스캐너", version 1.2.0. marketplace: metadata.version 1.2.0, stop-slop-ko description에 "리포트·에세이·블로그 같은 서술형 글도 다룬다" 추가.
- [ ] **Step 2** — README: 들어 있는 것 표의 stop-slop-ko 행에 서술형 언급, `### stop-slop-ko` 아래에 "내가 쓴 글 다듬기" 소절(리포트·블로그 전후 예시 각 1개, `--prose` 사용법과 문서 전체 WARN 기준, 종결어미 불변). 자동 적용 훅 문단에 "리포트 써줘", "블로그 글 다듬어줘" 예와 자소서 처리. English 절에 한 줄.
- [ ] **Step 3** — 허브 CLAUDE.md 표 stop-slop-ko 설명에 "서술형 글(리포트·블로그) 문체" 추가. `.gitignore`에 `*.packed.html`, `*.artifact.html`.
- [ ] **Step 4** — `python -m unittest discover tests` 전부 PASS, README를 `slop_scan.py` 로 스캔해 새 WARN 없음.
- [ ] **Step 5: 커밋** — `docs: 서술형 문체 README, 버전 1.2.0`

### Task 6: 교차 리뷰와 마무리

- [ ] codex-review 스킬로 브랜치 전체 교차 리뷰, 반영, 테스트 재실행
- [ ] 스펙·계획·검토 html 커밋(`docs: 서술형 문체 스펙과 계획`)
