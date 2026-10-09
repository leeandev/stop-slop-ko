# pptx 안전 편집 레시피 (python-pptx)

파워포인트 텍스트만 **서식 유지하며** 안전 치환. 표·그룹·다층 run 대응. (python-pptx 필요: `pip install python-pptx`)

## 원칙
1. **원본 백업 먼저** — `shutil.copyfile(src, bak)`.
2. **needle(고유 부분문자열) 매칭**으로 문단을 찾는다 — 슬라이드 번호가 파일마다 달라도(합본 14~17 ↔ 단독본 4~7) 같은 규칙 재사용.
3. **`run[0]` 서식 보존** — 문단 첫 run에 새 텍스트, 나머지 run은 `""`로 비움. 다층 run(잘게 쪼개진 문단)도 서식 유지.
4. **슬라이드 범위 화이트리스트** — 편집 대상 외 장은 원천 차단(다른 장 오손 방지).
5. needle이 **2곳 이상/0곳** 매칭이면 스킵 + 경고. 충돌 시 needle에 고유 어구(예: em-dash 포함 `예약 기능 — 요구사항 No.12`) 추가.
6. **검증** — 백업 대비 변경 슬라이드 격리 + 잔여 신호 문단 스캔.

## 재사용 템플릿
```python
# -*- coding: utf-8 -*-
import re, shutil
from pptx import Presentation

SRC = r"...deck.pptx"; BAK = SRC.replace(".pptx","_ORIG-backup.pptx")
ALLOWED = {14,15,16,17}          # 1-based 편집 대상 슬라이드
EDITS = [                         # (needle 고유부분문자열, 새 문단 전체)
    ("일관성을 확보함", "화면별 안내 문구, 버튼 위치, 용어 표기 기준 사전 확정"),
    # ...
]

def norm(s): return re.sub(r"\s+"," ",s).strip()
def iter_paras(shapes):
    for sh in shapes:
        if sh.shape_type == 6:                     # GROUP → 재귀
            yield from iter_paras(sh.shapes); continue
        if sh.has_text_frame:
            for p in sh.text_frame.paragraphs: yield p
        if sh.has_table:
            for row in sh.table.rows:
                for cell in row.cells:
                    for p in cell.text_frame.paragraphs: yield p
def set_para(p, new):                              # run[0] 서식 보존
    if not p.runs: return False
    p.runs[0].text = new
    for r in p.runs[1:]: r.text = ""
    return True

shutil.copyfile(SRC, BAK)                          # 1. 백업
prs = Presentation(BAK); slides = list(prs.slides) # 백업(원본)에서 로드 → 라이브에 저장
issues=[]; ok=0
for needle, new in EDITS:
    m=[p for i,sl in enumerate(slides,1) if i in ALLOWED
         for p in iter_paras(sl.shapes) if norm(needle) in norm(p.text)]
    if len(m)==1: set_para(m[0], new); ok+=1
    else: issues.append((needle, len(m)))          # 0=오타, >1=충돌
prs.save(SRC)
print(f"applied={ok}/{len(EDITS)} issues={issues}")
```

## 검증 스니펫
```python
# 변경 범위 격리: 백업 대비 어떤 슬라이드가 바뀌었나
def stext(sl):
    t=[]
    def w(shs):
        for sh in shs:
            if sh.shape_type==6: w(sh.shapes); continue
            if sh.has_text_frame and sh.text_frame.text.strip(): t.append(sh.text_frame.text)
            if sh.has_table:
                for r in sh.table.rows: t.append(" | ".join(c.text for c in r.cells))
    w(sl.shapes); return "\n".join(t)
L=list(Presentation(SRC).slides); B=list(Presentation(BAK).slides)
print("changed:", [i+1 for i in range(len(L)) if stext(L[i])!=stext(B[i])])  # ALLOWED와 일치해야 함
```

## 함정
- **콘솔 cp949 인코딩** → 한글/특수문자 출력 실패. UTF-8 파일로 덤프 후 Read 도구로 확인.
- **다층 run** 문단은 서식 균일 확인 후 병합(볼드·색 다르면 개별 처리). `run[0]` 색·크기·폰트를 그대로 물려받음.
- 표 셀은 `" | "`로 조인해 스캔하면 `" · "`·`" — "`가 **오검출** → 문단 단위로 재스캔.
- **python-pptx 재저장 = XML 재직렬화**: 파트당 ±1바이트, **파트 드롭 없음**. 파일 크기 감소는 압축률 차이일 뿐. 단 레이아웃·도형 위치는 파워포인트로 **육안 확인** 권장(텍스트만 프로그램 검증됨).
- 표의 `—`(해당없음)·붙임 middot(`성능·품질`)은 슬롭 아님 → needle에 걸리지 않게 주의.
