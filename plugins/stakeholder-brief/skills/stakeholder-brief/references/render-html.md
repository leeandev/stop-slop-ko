# HTML 아티팩트 렌더

자기완결 단일 HTML(외부 의존 0). 스파인 순서대로 섹션 카드 + 상태색 + 진행률 바 + 부록 `<details>` 접기. 빠른 공유용(브라우저로 열거나 그대로 전달).

## 원칙
- **인라인 CSS만**(외부 CDN·폰트 링크 금지 → 폐쇄망·오프라인에서도 열림). 시스템 폰트 스택.
- 화면 스캔 최적화: 1p 요약을 최상단 큰 카드로, 현황은 표, 부록은 기본 접힘.
- 색은 상태 표시에만 절제해서(완료=초록, 진행=노랑, 지연=빨강, 미정=회색). 과한 그라데이션·이모지 남발 금지(AI 티).
- 인쇄 대비 `@media print` 한 줄이라도.

## 스켈레톤 (채워서 사용)
```html
<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{제목}</title>
<style>
:root{--g:#1f9d55;--y:#c98a00;--r:#c0392b;--w:#8a8f98;--ink:#1a1a1a;--line:#e5e7eb;--bg:#fafafa}
*{box-sizing:border-box}body{margin:0;font-family:'Malgun Gothic','맑은 고딕',system-ui,sans-serif;color:var(--ink);background:var(--bg);line-height:1.6}
.wrap{max-width:900px;margin:0 auto;padding:32px 24px}
h1{font-size:22px;margin:0 0 4px}.sub{color:var(--w);font-size:13px;margin-bottom:24px}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:18px 20px;margin:14px 0}
.summary{border-left:4px solid var(--g);background:#fff}
h2{font-size:15px;margin:0 0 10px;color:#111}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--w);font-weight:600;background:#f6f7f9}
.badge{display:inline-block;padding:1px 8px;border-radius:20px;font-size:12px;color:#fff}
.b-g{background:var(--g)}.b-y{background:var(--y)}.b-r{background:var(--r)}.b-w{background:var(--w)}
.bar{height:8px;background:#eef0f2;border-radius:6px;overflow:hidden}.bar>i{display:block;height:100%;background:var(--g)}
details{margin:8px 0}summary{cursor:pointer;font-weight:600;font-size:14px}
ul{margin:6px 0 6px 18px;padding:0}li{margin:3px 0}
@media print{body{background:#fff}.card{break-inside:avoid;border-color:#ccc}}
</style></head><body><div class="wrap">
<h1>{제목}</h1><div class="sub">{프로젝트} · {대상 청중} · {날짜}</div>

<div class="card summary"><h2>요약</h2>
<ul><li>{지금 어디}</li><li>{무엇 결정됨}</li><li>{핵심 리스크}</li></ul></div>

<div class="card"><h2>배경·목적</h2><p>{...}</p></div>

<div class="card"><h2>진행 현황</h2>
<table><tr><th>항목</th><th>상태</th><th>비고</th></tr>
<tr><td>{마일스톤}</td><td><span class="badge b-g">완료</span></td><td>{...}</td></tr>
<tr><td>{...}</td><td><span class="badge b-y">진행</span></td><td>{...}</td></tr>
</table></div>

<div class="card"><h2>합의된 결정</h2><ul><li>{...}</li></ul></div>
<div class="card"><h2>미결 · 리스크</h2><ul><li>{...}</li></ul></div>
<div class="card"><h2>다음 단계</h2><ul><li>{...}</li></ul></div>

<div class="card"><details><summary>부록 — 기술 상세 · 용어집</summary>
<p>{청중이 비개발자면 여기로 내림}</p></details></div>
</div></body></html>
```

## 채우기 규칙
- 상태 배지: 완료=`b-g`, 진행=`b-y`, 지연=`b-r`, 미정=`b-w`. 원문 근거대로.
- 진행률 바가 필요하고 **원문에 %가 있으면**: `<div class="bar"><i style="width:70%"></i></div>`. 없으면 단계명만.
- 저장은 `.html`로 사용자 문서 폴더에. 파일 열어 육안 확인 권장.
- 마지막에 `stop-slop-ko`로 본문 어조 정리.
