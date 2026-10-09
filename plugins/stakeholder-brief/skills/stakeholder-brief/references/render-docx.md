# DOCX 렌더 (python-docx)

공식 산출물·납품용. 스파인 순서대로 제목·표·불릿. (`pip install python-docx`)

## 원칙
- 회사 서식이 있으면 **기존 DOCX 템플릿을 열어 채우는 방식** 우선(스타일 유지). 없으면 아래처럼 신규 작성.
- 상태는 텍스트 라벨(완료/진행/지연/미정)에 셀 배경이나 글자색을 더해 표시. 상태 이모지는 쓰지 않는다. 과한 서식 금지.
- 표(현황·마일스톤) + 불릿(결정·리스크·다음 단계) 조합. 부록은 마지막 섹션(제목 스타일로 구분).
- 숫자·결정은 원문 근거대로. 지어내기 금지(consensus-spine.md 규칙).

## 신규 작성 템플릿
```python
# -*- coding: utf-8 -*-
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()
# 기본 폰트(한글)
doc.styles['Normal'].font.name = '맑은 고딕'
doc.styles['Normal'].font.size = Pt(10)

def h(text, level=1):
    p = doc.add_heading(text, level=level); return p

doc.add_heading('{제목}', 0)
sub = doc.add_paragraph('{프로젝트} · {대상 청중} · {날짜}')
sub.runs[0].font.color.rgb = RGBColor(0x8a,0x8f,0x98)

h('요약', 1)
for line in ['{지금 어디}', '{무엇 결정됨}', '{핵심 리스크}']:
    doc.add_paragraph(line, style='List Bullet')

h('배경·목적', 1); doc.add_paragraph('{...}')

h('진행 현황', 1)
rows = [('항목','상태','비고'),
        ('{마일스톤}','완료','{...}'),
        ('{...}','진행','{...}')]
t = doc.add_table(rows=0, cols=3); t.style = 'Light Grid Accent 1'
for r in rows:
    cells = t.add_row().cells
    for i,v in enumerate(r): cells[i].text = v

for title, items in [('합의된 결정', ['{...}']),
                     ('미결 · 리스크', ['{...}']),
                     ('다음 단계', ['{...}'])]:
    h(title,1)
    for it in items: doc.add_paragraph(it, style='List Bullet')

h('부록 — 기술 상세 · 용어집', 1)
doc.add_paragraph('{청중이 비개발자면 여기로 내림}')

doc.save(r'{출력경로}.docx')
```

## 기존 템플릿 채우기(있을 때)
- `Document(template_path)`로 열고, placeholder 문단/표를 찾아 텍스트만 교체(스타일 보존).
- 서식이 복잡해 python-docx로 스타일이 깨지면 Word COM(Windows)으로 템플릿을 열어 채우는 방식을 쓴다.

## 마무리
- 저장 후 Word/COM으로 한 번 열어 표·서식 육안 확인 권장.
- 본문 어조는 `stop-slop-ko`로 정리.
