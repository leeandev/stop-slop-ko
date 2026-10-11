#!/usr/bin/env python3
# UserPromptSubmit hook: 한국어 문서 작성·수정 요청이면 문서 스킬 사용 순서를 컨텍스트로 주입한다.
#   청중이 정해진 공유용 문서 -> stakeholder-brief 먼저, stop-slop-ko 마지막
#   그 밖의 문서 산출물       -> stop-slop-ko 생성 모드
# 판정은 (문서 키워드 또는 청중 키워드) + 작성 동사. `--selftest`로 판정표를 확인할 수 있다.
# 자소서 요청은 jasoseo 플러그인이 설치·활성화돼 있으면 그쪽 몫이라 끼어들지 않는다.
import sys, json, os, re
from pathlib import Path

DOC = re.compile(
    r"회의록|보고서|주간보고|제안서|기획서|계획서|설계서|정의서|결과서|명세서|가이드\s*문서|사용\s*가이드|매뉴얼|"
    r"안내문|공문|산출물|메일|이메일|초안|발표\s*자료|장표|슬라이드|\bppt|pptx|파워포인트|"
    r"엑셀|xlsx|스프레드시트|docx|워드\s*(문서|파일)|\.hwp|md\s*파일|\.md\b|마크다운|README", re.I)
AUDIENCE = re.compile(
    r"(직원|사내|내부|팀원|타팀|경영진|임원|고객사?|PM|현업|신입|저년차|이해관계자|발주처)\s*(공유\s*)?용|"
    r"공유용|브리프|소개\s*(자료|문서)|보고용|설명\s*자료|온보딩\s*(문서|자료)", re.I)
VERB = re.compile(r"만들|작성|써\s*줘|써줘|쓰고|정리|초안|생성|뽑아|다듬|편집|수정|고쳐|업데이트|반영|옮겨|채워")
TONE = re.compile(r"AI\s*티|AI가\s*쓴|번역투|톤(에|을|으로)?\s*(맞|통일)|문체\s*통일", re.I)
OPT_OUT = re.compile(r"stop-?slop[^\n]{0,15}(빼|없이|말고|제외|끄)|원문\s*그대로|문구\s*그대로")
# 자소서는 jasoseo가 설치·활성화돼 있으면 그쪽 몫. 없으면 서술형 글로 본다.
JASOSEO = re.compile(r"자소서|자기\s*소개서")
# 서술형 글. 개조식 문서 키워드(FORMAL)가 같이 오면 개조식이 이긴다("과제 보고서").
PROSE = re.compile(r"리포트|레포트|에세이|과제|소논문|독후감|감상문|블로그\s*(글|포스트|포스팅)|칼럼|기고문?")
FORMAL = re.compile(r"회의록|보고서|주간보고|제안서|기획서|계획서|설계서|정의서|결과서|명세서|매뉴얼|안내문|공문|"
                    r"장표|슬라이드|\bppt|pptx|파워포인트|엑셀|xlsx|스프레드시트", re.I)
JASOSEO_ID = "jasoseo@stop-slop-ko"

# 플러그인 루트 기준: hooks/ 옆의 skills/stop-slop-ko/scripts/slop_scan.py
SCANNER = (Path(__file__).resolve().parent.parent / "skills" / "stop-slop-ko" / "scripts" / "slop_scan.py").as_posix()
# 훅을 실행 중인 인터프리터로 안내한다(python3만 있는 환경에서 `python`이 없을 수 있음)
PYTHON = Path(sys.executable).as_posix() if sys.executable else "python3"
SCAN = f"`\"{PYTHON}\" \"{SCANNER}\" <파일>`"
SCAN_PROSE = f"`\"{PYTHON}\" \"{SCANNER}\" --prose <파일>`"
MESSAGES = {
    "brief": (
        "[문서 스킬 라우팅] 청중이 정해진 공유용 문서 요청으로 판정됨(키워드: {kw}). "
        "순서: 1) stakeholder-brief 스킬이 있으면 먼저 로드해 청중 렌즈와 문서 유형(합의형/가이드형)을 정하고 구조를 잡는다. "
        "(없으면 이 단계는 건너뛴다) 2) 문장은 stop-slop-ko 기준으로 쓰고 마지막 톤 패스로 적용한다. "
        f"3) 결과 파일을 {SCAN}로 검증해 PASS/FAIL을 보고한다. 문서를 쓰지 않는 요청이면 무시."
    ),
    "brief_explicit": (
        "[문서 스킬 라우팅] stakeholder-brief 명시 호출. 구조를 잡은 뒤 마지막 톤 패스로 stop-slop-ko를 적용하고 "
        f"{SCAN}로 검증해 PASS/FAIL을 보고할 것."
    ),
    "slop": (
        "[stop-slop-ko 자동 적용] 한국어 문서 산출물 작성/수정 요청으로 판정됨(키워드: {kw}). "
        "문서에 들어갈 한국어 문장을 쓰기 전에 stop-slop-ko 스킬을 로드해 요청에 맞는 모드"
        "(새로 쓰기=생성, 기존 문서 다듬기=정제, 다른 문서 문체에 맞추기=톤 맞춤)로 작업하고, "
        f"파일을 만든 뒤 {SCAN}로 검증해 WARN을 고친 다음 결과(PASS/FAIL)를 보고할 것. "
        "docx/pptx/xlsx 스킬과 함께 쓴다. 문서 텍스트를 쓰지 않는 요청(읽기, 분석, 코드)이면 무시."
    ),
    "prose": (
        "[stop-slop-ko 자동 적용] 한국어 서술형 글(리포트, 에세이, 자소서, 블로그, 칼럼) 작성/수정 요청으로 판정됨(키워드: {kw}). "
        "stop-slop-ko 스킬을 로드해 레지스터를 서술형으로 정하고 references/prose-patterns.md를 따른다"
        "(새로 쓰기=생성, 다듬기=정제는 종결어미 불변, 다른 글 문체에 맞추기=톤 맞춤). 사실·주장·출처는 지어내지 않는다. "
        f"파일을 만들면 {SCAN_PROSE}로 검증해 결과(PASS/FAIL)를 보고할 것. 글을 쓰지 않는 요청이면 무시."
    ),
}


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
    if head.startswith("/stakeholder-brief"):
        return "brief_explicit", "/stakeholder-brief"
    verb = VERB.search(prompt)
    aud = AUDIENCE.search(prompt)
    if verb and aud:
        return "brief", aud.group(0)
    tone = TONE.search(prompt)
    if tone:
        return "slop", tone.group(0)
    doc = DOC.search(prompt)
    if verb and doc:
        return "slop", doc.group(0)
    return None


SELFTEST = [
    ("주간보고 회의록 docx로 만들어줘", "slop"),
    ("고객사 메일 초안 써줘", "slop"),
    ("설계서 3장 수정해줘", "slop"),
    ("발표용 ppt 만들어줘", "slop"),
    ("내부 직원 공유용으로 스킬 소개 md 파일 하나 만들어줘", "brief"),
    ("이 설계 md를 경영진용으로 정리해줘", "brief"),
    ("고객 PM용 브리프 HTML로 만들어줘", "brief"),
    ("/stakeholder-brief 설계서.md 고객PM용", "brief_explicit"),
    ("이 pptx 14~17장 AI 티 빼줘", "slop"),
    ("3장을 1장 톤에 맞춰줘", "slop"),
    ("경영진용 브리프 만들고 AI 티 없게", "brief"),
    ("이 엑셀 파일 읽어서 분석해줘", None),
    ("/stop-slop-ko 이 문서", None),
    ("pptx 만들어줘 stop-slop 빼고", None),
    ("gradle 빌드 에러 고쳐줘", None),
    ("/jasoseo A사 2번 초안 써줘", None),
    ("자소서 초안 써줘", None),
    ("자기소개서 1번 초안 다듬어줘", None),
    ("자기 소개서 메일로 보낼 초안 만들어줘", None),
    ("리포트 초안 써줘", "prose"),
    ("에세이 다듬어줘", "prose"),
    ("블로그 글 AI 티 빼줘", "prose"),
    ("칼럼 써줘", "prose"),
    ("과제 보고서 써줘", "slop"),
    ("리포트 읽고 요약만 해줘", None),
    ("자소서 초안 써줘", "prose", False),
    ("자기소개서 1번 다듬어줘", "prose", False),
]


def selftest():
    fails = 0
    for prompt, want, *state in SELFTEST:
        jas = state[0] if state else True
        got = route(prompt, jasoseo=jas)
        got_kind = got[0] if got else None
        ok = got_kind == want
        fails += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {str(got_kind):15} {prompt}{'' if jas else ' (jasoseo 없음)'}")
    print(f"RESULT: {'PASS' if not fails else 'FAIL'} ({len(SELFTEST) - fails}/{len(SELFTEST)})")
    return 1 if fails else 0


def main():
    if "--selftest" in sys.argv:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.exit(selftest())
    try:
        hook = json.loads(sys.stdin.buffer.read().decode("utf-8", errors="replace"))
    except Exception:
        sys.exit(0)
    hit = route(hook.get("prompt") or "")
    if not hit:
        sys.exit(0)
    kind, kw = hit
    ctx = MESSAGES[kind].format(kw=kw)
    out = {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": ctx}}
    # ensure_ascii: 콘솔 코드페이지와 무관하게 안전한 ASCII JSON
    sys.stdout.write(json.dumps(out))


if __name__ == "__main__":
    main()
