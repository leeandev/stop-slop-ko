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


class ParagraphGrouping(Base):
    def test_md_wrapped_lines_are_one_paragraph(self):
        p = Path(tempfile.mkdtemp()) / "t.md"
        p.write_text(FILLER + "\n또한 한 줄.\n따라서 두 줄.\n그러므로 세 줄.\n", encoding="utf-8")
        self.assertNotIn("PROSE_CONNECTOR", [h[1] for h in S.scan(p, True, True)])

    def test_blank_line_paragraphs_in_one_cell(self):
        paras = [("A1", "\n\n".join([FILLER, "또한 하나.", "또한 둘.", "또한 셋."]))]
        self.assertIn("PROSE_CONNECTOR", [h[1] for h in S.prose_totals(S.split_paragraphs(paras), True)])


class ReviewFixes(Base):
    C3 = ["또한 하나.", "나아가 둘.", "따라서 셋."]

    def write(self, name, text):
        p = Path(tempfile.mkdtemp()) / name
        p.write_text(text, encoding="utf-8")
        return p

    def test_md_table_cells_not_counted(self):
        table = "\n".join(["| 항목 | 설명 |", "|---|---|"] + [f"| 항목{i} | 설명입니다 |" for i in range(4)])
        p = self.write("t.md", "\n\n".join([FILLER] + self.C3) + "\n\n" + table + "\n")
        self.assertIn("PROSE_CONNECTOR", [h[1] for h in S.scan(p, True, True)])

    def test_txt_single_newline_paragraphs(self):
        p = self.write("t.txt", "\n".join([FILLER] + self.C3) + "\n")
        self.assertIn("PROSE_CONNECTOR", [h[1] for h in S.scan(p, True, True)])

    def test_front_matter_skipped(self):
        p = self.write("t.md", "---\ntitle: 새 도구 후기\n---\n\n“실패는 성공의 어머니”라는 말이 있다.\n")
        self.assertIn("PROSE_QUOTE_OPEN", [h[1] for h in S.scan(p, True, True)])

    def test_blockquote_open(self):
        self.assertIn("PROSE_QUOTE_OPEN", self.codes(["> “실패는 성공의 어머니”", FILLER]))

    def test_front_matter_still_scanned_without_prose(self):
        p = self.write("t.md", "---\ntitle: 재택근무 — 후기\n---\n")
        self.assertIn("EMDASH", [h[1] for h in S.scan(p, False, False)])


class Cli(Base):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True)

    def test_exit_codes(self):
        p = self.md(body(700) + ["맞다고 생각한다."] * 3)
        self.assertEqual(self.run_cli(str(p)).returncode, 0)
        self.assertEqual(self.run_cli(str(p), "--prose").returncode, 1)


if __name__ == "__main__":
    unittest.main()
