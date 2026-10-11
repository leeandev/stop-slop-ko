# stop-slop-ko

한국어 실무문서에서 "AI가 쓴 티"를 걷어내는 Claude Code 스킬.

회의록, 보고서, 제안서, 메일, pptx/docx/xlsx를 Claude에게 맡기면 em-dash(`—`), 공백 가운뎃점 나열(` · `), `★`와 이모지, `~을 통하여` 같은 번역투가 섞여 나옵니다. 이 스킬은 그런 문장을 처음부터 쓰지 않게 하고, 이미 쓴 문서는 내용을 건드리지 않고 문장부호와 번역투만 고칩니다.

[hardikpandya/stop-slop](https://github.com/hardikpandya/stop-slop)(영어)의 한국어판입니다. 규칙을 그대로 옮기지 않고 한국어 개조식 문서에 맞게 다시 만들었습니다.

> English summary: Korean version of [stop-slop](https://github.com/hardikpandya/stop-slop). A Claude Code plugin that keeps AI tells (em-dashes, spaced middot lists, decorative emoji, translationese) out of Korean business documents, with a scanner for docx/pptx/xlsx/md. See [English](#english) below.

## Before / After

```diff
- 본 과제는 사내 도서 대여 앱의 검색 구조를 개선하여 사용 편의성을 제고하고 — 대여 절차를 간소화하는 것을 목표로 함.
+ 사내 도서 대여 앱의 검색 구조를 바꿔 쓰기 편하게 하고 대여 절차를 줄이는 것을 목표로 함.

- - ★ 검색 속도 개선 · 예약 기능 추가 · 반납 알림 강화
+ - 검색 속도 개선, 예약 기능 추가, 반납 알림 강화

- - 기존 화면 대비 메뉴 구성이 상이하여 사용자 안내가 필요함
+ - 메뉴 구성이 기존 화면과 달라 사용자 안내가 필요함

- - 새 검색 엔진을 통하여 3,000 권 목록을 1초 안에 조회 가능해짐 ✅
+ - 새 검색 엔진으로 3,000권 목록을 1초 안에 조회 가능

- - 대여 기록 관리에 있어서 확인 절차가 추가되어짐
+ - 대여 기록 확인 절차 추가됨

- - React 와 SQLite 를 사용함
+ - React와 SQLite를 사용함

- 이번 개선은 사내 독서 문화 활성화의 핵심이라 할 수 있다.
+ 이번 개선으로 사내 도서를 찾고 빌리기가 쉬워짐.
```

포함된 스캐너 `slop_scan.py`로 두 문서를 검사한 결과입니다. 문서 원본은 [`examples/`](examples/)에 있고, 출력에서 항목별 조치 안내 줄은 생략했습니다.

```
== before.md: WARN 9, INFO 1
  [WARN] EMDASH @ L5: …검색 구조를 개선하여 사용 편의성을 제고하고 — 대여 절차를 간소화하는 것을 목표로 함.
  [WARN] STAR @ L9: - ★ 검색 속도 개선 · 예약 기능 추가 · 반납…
  [WARN] MIDDOT_SPACED2 @ L9: - ★ 검색 속도 개선 · 예약 기능 추가 · 반납 알림 강화
  [INFO] TL_DAEBI_SANGI @ L10: - 기존 화면 대비 메뉴 구성이 상이하여 사용자 안내가 필요함
  [WARN] EMOJI @ L11: …,000 권 목록을 1초 안에 조회 가능해짐 ✅
  [WARN] TL_TONGHAYEO @ L11: - 새 검색 엔진을 통하여 3,000 권 목록을 1초 안에 조회 가능해…
  [WARN] TL_ISSEO @ L12: - 대여 기록 관리에 있어서 확인 절차가 추가되어짐
  [WARN] TL_DOEEOJI @ L12: - 대여 기록 관리에 있어서 확인 절차가 추가되어짐
  [WARN] PARTICLE_SPACE @ L13: - React 와 SQLite 를 사용함
  [WARN] TL_HALSUITDA @ L17: 이번 개선은 사내 독서 문화 활성화의 핵심이라 할 수 있다.
RESULT: FAIL (WARN 9)

== after.md: WARN 0, INFO 0
RESULT: PASS (WARN 0)
```

## 영어판 규칙을 그대로 쓰면 안 되는 이유

영어 stop-slop은 "능동태로, 짧게, 직설적으로"를 권합니다. 이걸 한국어 보고서에 그대로 적용하면 `정의함`이 `정의한다`로 바뀌고, 오히려 더 어색해집니다.

- **`~함/~됨` 개조식은 슬롭이 아닙니다.** 한국 공식문서의 정상 문체입니다. 정제 모드는 종결어미를 절대 바꾸지 않습니다.
- **한국어 슬롭의 신호는 문장부호, 번역투, 상투구입니다.** em-dash, 공백 가운뎃점 나열, `★`, `~에 있어서`, `~되어지다`, 조사 앞 공백(`React 와`) 같은 것들입니다.
- **영어판의 "3항목 나열 금지", "not X but Y 금지"는 한국어 요구사항·스펙 열거에 쓰지 않습니다.** 그건 문체가 아니라 내용입니다.
- **붙임 복합어는 보존합니다.** `성능·품질`, `원천·대상`의 가운뎃점은 나열 구분자가 아닙니다.

## 들어 있는 것

이 저장소는 Claude Code 플러그인 마켓플레이스이고, 플러그인 세 개가 들어 있습니다. 필요한 것만 설치하면 됩니다.

| 플러그인 | 하는 일 |
|---|---|
| **stop-slop-ko** | 한국어 문서를 쓸 때(생성), 다듬을 때(정제), 다른 문서 톤에 맞출 때(톤 맞춤) 문체 규칙을 적용. 리포트, 에세이, 블로그 같은 서술형 글도 다룸. 스캐너와 자동 적용 훅 포함 |
| **stakeholder-brief** | 설계서, 분석 문서, 진행 현황을 경영진, 고객 PM, 타팀 개발자 등 정해진 청중 눈높이로 다시 구성해 HTML/DOCX/MD로 출력. 마지막 문체 정리는 stop-slop-ko에 맡김 |
| **jasoseo** | 자소서를 대신 지어 쓰지 않고, 인터뷰로 본인 경험을 꺼내 경험 은행에 모은 뒤 본인 말투로 초안을 씀. 글자 수 계산기 포함 |

### stop-slop-ko

세 가지 모드가 있습니다.

- **생성 모드**: 회의록, 보고서, 메일을 새로 쓸 때 처음부터 규칙대로 씁니다. 파일을 만든 뒤 스캐너로 검사하고 결과를 `PASS`/`FAIL`로 보고합니다.
- **정제 모드**: 이미 있는 문서에서 부호, 번역투, 상투구만 고칩니다. 숫자, 요구사항 번호, 기술용어, 종결어미는 그대로 둡니다.
- **톤 맞춤 모드**: 동료가 쓴 다른 장이나 기존 승인 문서의 문체(종결어미, 부호, 목록기호 등 6가지 축)를 뽑아 내 글을 거기에 맞춥니다.

**스캐너** `slop_scan.py`: docx(본문, 표, 머리글, 각주), pptx(슬라이드 순서, 표), xlsx(셀, 도형), md, txt, html을 문단 단위로 검사합니다. 파이썬 표준 라이브러리만 씁니다.

```bash
python plugins/stop-slop-ko/skills/stop-slop-ko/scripts/slop_scan.py 보고서.docx --info
```

- exit 0 = PASS, 1 = FAIL(WARN 있음), 2 = 입력 오류
- 상투구, 과한 명사화, 기계적인 3단 병렬은 스캐너가 못 잡습니다. 그 부분은 스킬이 읽고 판단합니다.

**내가 쓴 글 다듬기**: 리포트, 과제, 에세이, 블로그 글, 칼럼처럼 문단으로 이어 쓰는 글도 같은 세 모드로 다룹니다. 개조식으로 바꾸지 않고 문단 서술을 유지하며, 다듬을 때 `~다`와 `~습니다` 같은 종결어미는 그대로 둡니다. 서술형 글에 자주 끼는 상투구를 걷어냅니다.

| 전 | 후 |
|---|---|
| 오늘은 Docker 볼륨에 대해 알아보겠습니다. 정말 많은 분들이 헷갈려 하시는 부분입니다. | (삭제) 본론 "컨테이너를 지우면 안에 쓴 파일도 함께 사라집니다."부터 시작 |
| 기록이 남으면서 결정이 뒤집히는 일이 줄었다고 생각한다. … 이번 경험을 통해 소통의 중요성을 깨달았다. | 기록이 남으면서 결정이 뒤집히는 일이 줄었다. |

스캐너에 `--prose`를 붙이면 서술형 신호도 검사합니다.

```bash
python plugins/stop-slop-ko/skills/stop-slop-ko/scripts/slop_scan.py 리포트.md --prose --info
```

- INFO(위치만 알림): 교훈형 마무리("~의 중요성을 깨달았다"), "단순한 ~이 아닌", 명언으로 시작하는 첫 문단, 빈 강조어("정말", "매우"), 리포트·블로그 상투구
- WARN(글 전체 기준): "~라고 생각한다"가 3회 이상이면서 1,000자당 1회 이상, 연결어("또한", "나아가")로 시작하는 문단이 3개 이상이면서 전체 문단의 25% 이상. 긴 글일수록 기준이 올라가서 정상적인 빈도는 걸리지 않습니다
- 사실, 수치, 출처를 지어내지 않습니다. 고칠 문장에 근거가 없으면 지우거나 묻습니다

**자동 적용 훅**: "회의록 만들어줘", "보고서 pptx로", "AI 티 빼줘" 같은 요청을 감지하면 스킬을 쓰라고 Claude에게 알려 줍니다. "경영진용", "공유용", "브리프"처럼 청중이 정해진 요청이면 stakeholder-brief를 먼저 쓰라고 안내합니다. "리포트 써줘", "블로그 글 다듬어줘" 같은 서술형 요청이면 서술형 문체로 안내합니다. 자소서 요청은 jasoseo가 설치돼 있으면 jasoseo에 맡기고, 없으면 서술형 글로 다룹니다. 요청에 "stop-slop 빼고"나 "원문 그대로"를 넣으면 끼어들지 않습니다.

### stakeholder-brief

- 청중 4종(경영진/스폰서, 고객 PM, 저년차·타팀 개발자, 고객 개발자)별로 전문용어를 얼마나 풀지, 어디까지 부록으로 내릴지 정합니다.
- 문서 유형은 두 가지입니다. 진행과 합의를 전하는 **합의형**(요약 → 현황 → 합의된 결정 → 미결 → 다음 단계), 도구나 절차를 알려 주는 **가이드형**(한눈에 보기 → 왜 필요한가 → 설치 → 사용 예시 → 한계)입니다.
- **원문에 없는 진척률, 일정, 결정은 지어내지 않습니다.** 없으면 "미정", "확인 필요"로 남깁니다.

### jasoseo

자소서를 Claude에게 통째로 맡기면 누구나 쓸 수 있는 글이 나옵니다. 기업이 거르는 글이 바로 그런 글입니다. jasoseo는 반대로 갑니다.

- **인터뷰**: 문항 유형(지원동기, 성장과정, 직무역량, 갈등·실패, 입사 후 포부)에 맞춰 한 번에 1~2개씩 묻습니다. "열심히 했다", "소통했다" 같은 답에는 "예를 들면요?"로 다시 묻습니다.
- **경험 은행**: 답은 작업 폴더의 `jasoseo/stories.md`에 경험 카드로 쌓입니다. 다음 회사 자소서에서 다시 꺼내 씁니다.
- **초안**: 카드에 있는 사실과 본인이 한 말로만 씁니다. 카드에 없는 숫자나 역할은 만들지 않고 `[확인 필요: ...]`로 비워 둡니다.
- **글자 수**: `count.py`가 공백 포함, 공백 제외, 바이트까지 셉니다. 초안은 제한의 90~100%에 맞춥니다.
- **점검 리포트**: 근거 없는 문장, 뻔한 문장, 문체 문제를 짚습니다.

```
[점검] A사 백엔드 2번
- 글자 수: 공백 포함 662/700자 (94%), 범위 안
- 근거 없는 문장: 3문단 "팀을 이끌며" (S03에 리더 역할 없음)
- 확인 필요: 1곳 (기능 추가를 원한 팀원 수)
- 뻔한 문장: "소통의 중요성을 깨달았습니다" (S03의 본인 말로 바꾸기 제안)
- 문체: 위반 없음
```

AI 검사기를 피하는 도구가 아닙니다. 본인 경험과 말투로 쓴 글이 면접까지 버팁니다. stop-slop-ko 없이 혼자 동작합니다.

## 설치

Claude Code 입력창에 한 줄씩 입력합니다.

**1단계. 마켓플레이스 등록 (필수, 한 번만)**

이 저장소를 플러그인 목록으로 등록합니다. 아직 아무것도 설치되지 않습니다.

```
/plugin marketplace add leeandev/stop-slop-ko
```

**2단계. 필요한 플러그인 설치 (골라서)**

| 이렇게 쓰려면 | 설치할 것 |
|---|---|
| 한국어 문서의 AI 티만 빼고 싶다 (대부분 이것) | stop-slop-ko만 |
| 경영진용, 고객 PM용 같은 공유 문서도 만들고 싶다 | 둘 다 |
| 자소서를 쓰려고 한다 | jasoseo (단독으로 동작) |

stop-slop-ko 설치 (기본):

```
/plugin install stop-slop-ko@stop-slop-ko
```

stakeholder-brief 설치 (공유 문서도 만들 때만 추가):

```
/plugin install stakeholder-brief@stop-slop-ko
```

jasoseo 설치 (자소서를 쓸 때):

```
/plugin install jasoseo@stop-slop-ko
```

stakeholder-brief만 따로 설치해도 동작은 하지만, 마지막 문체 정리를 stop-slop-ko에 맡기도록 만들어져 있어서 둘 다 설치하는 것을 권장합니다.

설치가 끝나면 Claude Code를 재시작합니다. `/plugin`을 열면 설치된 플러그인을 확인할 수 있습니다.

**요구 사항**
- 스캐너와 훅: Python 3.8 이상(macOS/Linux는 `python3`, Windows는 `python`을 찾아 씁니다)
- 자동 적용 훅은 `sh`로 실행됩니다. Windows는 Git Bash가 필요합니다(Git for Windows에 포함). Git Bash가 없으면 훅만 동작하지 않고, 스킬과 스캐너는 그대로 쓸 수 있습니다
- pptx 정제 레시피: `pip install python-pptx`
- DOCX 출력: `pip install python-docx`

## 사용 예

```
주간 회의록 docx로 만들어줘. 녹취는 meeting.txt
이 제안서 3장 AI 티 빼줘
이 블로그 글 다듬어줘. 파일은 post.md
14~17장을 1~13장 톤에 맞춰줘
이 설계 문서 경영진용 1페이지 브리프로 정리해줘
/stop-slop-ko:stop-slop-ko 보고서.md
자소서 써줘. A사 백엔드 2번 문항, 공백 포함 700자
/jasoseo:jasoseo
```

플러그인 스킬은 `플러그인:스킬` 이름으로 직접 부릅니다(`/stop-slop-ko:stop-slop-ko`, `/stakeholder-brief:stakeholder-brief`). 대부분은 위처럼 평소 말투로 요청하면 알아서 쓰입니다.

## English

**stop-slop-ko** is a Claude Code plugin marketplace with three plugins for Korean business writing.

- **stop-slop-ko**: removes AI tells from Korean documents. It has three modes: write (generate clean text from the start), de-slop (fix punctuation and translationese only, without touching facts or sentence endings), and tone-match (copy the style signature of a reference document). It also handles prose (reports, essays, blog posts, columns) without changing the sentence endings the author chose. It ships with `slop_scan.py`, a stdlib-only scanner for docx/pptx/xlsx/md/txt/html (`--prose` adds length-aware checks for prose clichés), and a prompt hook that routes document requests to the skill.
- **stakeholder-brief**: rewrites dev material (design docs, status, analyses) for one audience at a time (executives, customer PMs, other-team engineers, customer engineers) and renders HTML, DOCX, or MD. It never invents progress, dates, or decisions that the source does not contain.
- **jasoseo**: a Korean cover letter (자기소개서) coach. It interviews the user, stores their real experiences as reusable story cards, drafts only from those cards in the user's own voice, marks missing facts as `[확인 필요]` instead of inventing them, and counts characters the way Korean job sites do. It works without stop-slop-ko.

The English stop-slop rules ("prefer active voice", "avoid lists of three") backfire in Korean, where noun-ending bullet style (`~함/~됨`) is the normal register of official documents. This version targets the real Korean signals instead: em-dashes, spaced middot lists, decorative symbols, translationese, and spaces before particles.

```
/plugin marketplace add leeandev/stop-slop-ko      # register the marketplace (once)
/plugin install stop-slop-ko@stop-slop-ko         # the main plugin
/plugin install stakeholder-brief@stop-slop-ko    # optional: audience-specific briefs
/plugin install jasoseo@stop-slop-ko              # optional: Korean cover letter interviews
```

## 라이선스

MIT. 영어 원본 [hardikpandya/stop-slop](https://github.com/hardikpandya/stop-slop)(MIT)에서 아이디어를 가져왔습니다.
