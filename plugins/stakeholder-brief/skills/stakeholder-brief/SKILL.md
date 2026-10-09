---
name: stakeholder-brief
description: Use when turning dev/project material (design doc, analysis, plan, status, root-cause report, tool/skill docs) into a document for a specific audience such as executives, customer PMs, internal staff or other teams, or customer engineers. Leads document requests that name an audience, and stop-slop-ko runs last as the tone pass. Triggers include /stakeholder-brief, "고객PM/경영진용으로 정리해줘", "직원 공유용 md 만들어줘", "이해관계자 공유용 문서/브리프/소개 자료 만들어줘". Outputs HTML, DOCX, or MD.
---

# stakeholder-brief

개발 자료(`.md` 산출물, 설계·분석 문서, 도구·스킬 파일)를 **정해진 청중 눈높이의 공유 문서**(HTML/DOCX/MD)로 바꾸는 하네스. 어려운 건 렌더링이 아니라 **청중 눈높이 재구성 + 문서 유형에 맞는 재구조화**다.

**스킬 순서:** 청중이 정해진 문서 요청이면 이 스킬이 먼저 청중과 구조를 잡고, `stop-slop-ko`는 마지막 문체 패스로만 쓴다. 문장을 먼저 다듬고 구조를 나중에 잡으면 재구성 과정에서 다듬은 문장이 다시 흐트러진다.

## 핵심 원칙 (어기면 문서가 망함)
- **사실·숫자·결정은 원문에서만.** 원문에 없는 진척률·일정·수치·결정을 **지어내지 않는다.** 없으면 "미정 / 확인 필요"로 표기.
- 기술을 **추상화하되 왜곡하지 않는다.** 깊은 기술은 삭제가 아니라 **부록/접기**로.
- **한 번에 한 청중.** 청중이 바뀌면 다시 돌린다(한 문서에 여러 청중 욱여넣기 금지).

## 워크플로
1. **입력·청중 확정** — 원본(단일 .md 또는 관련 파일 묶음) + 대상 청중 지정. 청중 미지정이면 먼저 물어본다.
2. **문서 유형 결정** — 진행·합의를 공유하는 문서면 **합의형**(`references/consensus-spine.md`), 도구·절차·기능을 알려 주는 문서면 **가이드형**(`references/guide-spine.md`).
3. **청중 렌즈** — `references/audience-personas.md`로 {관심사·전문용어 예산·깊이·원하는 액션} 적용
4. **재구조화** — 고른 스파인에 원문 재배치 + 전문용어 번역 + so-what 추출 + 근거 추적(원문 위치)
5. **렌더** — HTML → `references/render-html.md` / DOCX → `references/render-docx.md` / MD → 아래 "MD 출력"
6. **톤 패스** — `stop-slop-ko` 스킬로 어조 정리 후 `slop_scan.py`로 스캔(한국어 개조식/서술체는 청중에 맞춤)
7. **검증** — 숫자·결정 원문 대조, 청중 눈높이 확인, **"지어낸 현황 없음" 자기점검**

## 합의 문서 스파인 (기본)
1. **1p 요약** (경영진 3줄: 지금 어디·무엇 결정됨·리스크)
2. 배경·목적
3. **진행 현황** (마일스톤·%·상태색)
4. **합의된 결정**
5. 미결 / 리스크
6. 다음 단계·일정
7. 부록 (기술 상세·용어집)

가이드형(도구·절차 소개)은 `references/guide-spine.md`: 한눈에 보기 → 왜 필요한가 → 무엇을 하나 → 설치·적용 → 사용 예시 → 주의·한계 → 문제 해결 → 부록.

## 청중 (한 번에 하나)
경영진/스폰서 · 고객 PM/이해관계자 · 저년차/타팀 개발자 · 고객 개발자 — 프로필·번역 강도는 `audience-personas.md`.

## 출력
- **HTML 아티팩트** — 자기완결 파일(상태색·진행률 바·부록 `<details>` 접기). 빠른 공유용.
- **DOCX** — python-docx. 공식 산출물·납품용.
- **MD** — 사내 리포·위키·메신저 공유용. 아래 "MD 출력".
- (PPTX가 필요하면 그때 추가. 현재 스코프 아님)

### MD 출력
- GFM 기준: 제목 번호(`## 1.`), 앞쪽 목차(앵커 링크), 섹션 사이 `---`, 표·코드블록. 같은 폴더에 기존 가이드가 있으면 그 구성을 따른다.
- 상태색은 이모지 대신 텍스트(`완료`, `진행`, `지연`, `미정`). 장식 이모지·★ 금지.
- 부록은 HTML의 `<details>` 대신 문서 끝 `## 부록` 절로.
- 명령어·경로·설정은 반드시 코드블록. 실제로 돌려 본 명령만 싣고, 못 돌린 건 "미검증"으로 표시.
- 저장 위치·파일명은 사용자 문서 규칙을 따른다(주제로 시작, 날짜·버전은 파일명에 넣지 않음).

## Common Mistakes
- stop-slop-ko로 문장부터 다듬고 구조를 나중에 잡음 → **순서: 이 스킬로 재구성 먼저, stop-slop-ko는 마지막**
- 가이드형 문서에 합의형 스파인(현황·합의 결정)을 억지로 끼움 → 문서 유형부터 정한다
- 원문에 없는 진척률·일정·결정을 그럴듯하게 지어냄 → **금지**, "미정"으로
- 기술을 과도하게 쳐내 부정확해짐 → 부록으로 내리되 사실 보존
- 여러 청중을 한 문서에 → 초점 흐림. 한 번에 한 청중
- 어조가 기계적 → 마지막에 `stop-slop-ko`
- "완료"를 원문 근거 없이 단정 → 원문에 근거 있는 것만 완료로
