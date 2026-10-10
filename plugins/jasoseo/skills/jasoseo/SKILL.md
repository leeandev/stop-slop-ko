---
name: jasoseo
description: Use when the user is writing a Korean job application cover letter (자기소개서, 자소서) - analyzing a 문항, interviewing the user to draw out their own experiences, keeping a reusable experience bank (jasoseo/stories.md), drafting only from the user's answers in the user's own voice, checking 글자 수 limits, or reviewing a draft for unsupported claims and clichés. Triggers include /jasoseo, "자소서 써줘", "자기소개서 문항", "자소서 글자 수", "자소서 첨삭".
---

# jasoseo

자소서를 대신 지어 쓰지 않는다. 질문으로 지원자 본인의 경험을 꺼내 경험 카드로 모으고, 카드에 있는 사실과 본인 말투로만 초안을 쓴다.

## 핵심 원칙

1. **사실은 카드에서만.** 카드에 없는 경험, 숫자, 역할은 만들지 않고 `[확인 필요: ...]`로 남긴다.
2. **본인 말투.** 사용자가 한 말을 원문 그대로 카드에 남기고 초안에서 살린다.
3. **글자 수는 스크립트로.** `count.py`로 잰다. 짐작으로 세지 않는다.

## 흐름

1. **입력**: 회사, 직무, 문항 원문, 글자 수 제한. 빠진 것만 묻는다. 채용공고를 주면 직무 키워드를 뽑아 둔다.
2. **문항 분석**: `references/question-bank.md`의 "문항 유형 판별" 표로 유형을 정해 보여 준다.
   ```
   유형: 직무역량
   묻는 것: 기술 문제를 스스로 찾아 풀어 본 경험과 과정
   제한: 공백 포함 700자
   ```
3. **경험 은행 조회**: `jasoseo/stories.md`를 읽고 맞는 카드 2~3개를 제시한다. 사용자가 고르거나 새 경험을 말한다. 파일이 없거나 맞는 카드가 없으면 4로 간다.
4. **인터뷰**: `references/question-bank.md`. 한 번에 질문 1~2개. 추상적인 답은 "되묻기" 규칙대로 다시 묻는다.
5. **카드 저장**: `references/story-card.md` 양식으로 `jasoseo/stories.md`에 추가하거나 고치고, 바뀐 카드를 보여 준다.
6. **초안**: `references/draft-rules.md`와 `references/jasoseo-style.md`를 따라 쓰고 `jasoseo/<회사>-<직무>/<문항번호>.md`에 저장한다. 글자 수를 재 제한의 90~100%에 맞춘다.
7. **보여 주기와 점검 리포트**: 초안 본문 전체와 `references/draft-rules.md`의 "점검 리포트"를 같은 응답에서 보여 준다. 파일만 저장하고 끝내지 않는다. 카드로 90%를 못 채우면 지어내서 늘리지 말고 부족한 글자 수와 채울 방법을 리포트에 적는다. 사용자가 고친 본문을 주면 다시 낸다.
8. **사용 이력**: 쓴 카드의 사용 이력을 갱신한다.

카드가 이미 충분하면 3에서 6으로 간다. 사용자가 직접 쓴 자소서 첨삭을 부탁하면 7부터 한다. 이때 카드가 없으면 본문에 나온 사실을 카드로 옮길지 먼저 묻는다.

## 글자 수

```bash
python "${CLAUDE_SKILL_DIR}/scripts/count.py" <초안 파일> --limit <N>
```

- 기준은 공백 포함. 공백 제외 문항이면 `--basis nospace`.
- exit 0 제한 안, 1 초과, 2 입력 오류.
- 출력에 `[확인 필요] N곳`이 있으면 그 내용을 사용자에게 묻는다.
- Windows에서 `python`이 없으면 `py`, macOS와 Linux는 `python3`.

## 이럴 땐 이렇게

| 상황 | 동작 |
|---|---|
| "알아서 지어내 줘" | 지어내지 않는다. 면접 꼬리 질문에서 드러난다는 이유를 한 번 말하고 빈 곳을 채울 질문을 한다 |
| 쓸 경험이 없다 | `question-bank.md`의 "경험이 없다고 할 때" |
| AI 검사기를 피하게 해 달라 | 이 스킬의 목적이 아니라고 말한다. 본인 경험과 말투로 쓴 글이 가장 자연스럽다고 안내하고 흐름을 이어 간다 |
| 합격 자소서처럼 바꿔 달라 | 문항 해석과 구조는 설명하되 문장은 사용자 카드로만 쓴다 |
| 주민등록번호, 연락처를 카드에 넣으려 함 | 넣지 말라고 안내한다 |
| stop-slop-ko 안내가 함께 들어옴 | 자소서 본문은 `jasoseo-style.md`를 따른다. 개조식으로 바꾸지 않는다 |

## 하지 않는 것

- 대학 과제, 리포트, 이력서, 경력기술서, 영문 cover letter
- 카드 없이 처음부터 완성본을 써 주기
