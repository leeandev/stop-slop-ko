# -*- coding: utf-8 -*-
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "plugins" / "jasoseo" / "skills" / "jasoseo" / "scripts" / "count.py"
sys.path.insert(0, str(SCRIPT.parent))

import count as C  # noqa: E402


class CountTest(unittest.TestCase):
    def test_hangul_and_spaces(self):
        c = C.count("안녕 하세요")
        self.assertEqual(c["space"], 6)
        self.assertEqual(c["nospace"], 5)
        self.assertEqual(c["utf8"], 16)
        self.assertEqual(c["euckr"], 11)

    def test_newlines(self):
        c = C.count("가나\n다라")
        self.assertEqual(c["space"], 5)
        self.assertEqual(c["space_no_newline"], 4)
        self.assertEqual(c["nospace"], 4)

    def test_crlf_normalized(self):
        self.assertEqual(C.count("가\r\n나")["space"], 3)

    def test_heading_and_comment_removed(self):
        text = "# A사 2번\n<!-- 제한: 700 -->\n\n본문입니다.\n"
        self.assertEqual(C.count(text)["space"], 6)

    def test_multiline_comment_removed(self):
        text = "<!--\n메모\n-->\n본문"
        self.assertEqual(C.count(text)["space"], 2)

    def test_bare_hash_line_keeps_next_line(self):
        self.assertEqual(C.count("#\n본문입니다.\n다음")["space"], 9)

    def test_inline_comment_keeps_newline(self):
        self.assertEqual(C.count("앞<!-- 메모 -->\n뒤")["space"], 3)

    def test_emoji_not_in_euckr(self):
        c = C.count("좋아👍")
        self.assertEqual(c["space"], 3)
        self.assertEqual(c["non_euckr"], ["👍"])
        self.assertEqual(c["euckr"], 6)

    def test_gaps(self):
        self.assertEqual(C.count("팀원 [확인 필요: 인원 수]명")["gaps"], 1)

    def test_empty(self):
        self.assertEqual(C.count("# 제목만\n")["space"], 0)

    def test_judge(self):
        self.assertEqual(C.judge(630, 700), "ok")
        self.assertEqual(C.judge(629, 700), "under")
        self.assertEqual(C.judge(700, 700), "ok")
        self.assertEqual(C.judge(701, 700), "over")


class CliTest(unittest.TestCase):
    def run_cli(self, text, *args, encoding="utf-8"):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "q.md"
            p.write_bytes(text.encode(encoding))
            r = subprocess.run([sys.executable, str(SCRIPT), str(p), *args], capture_output=True)
            return r.returncode, r.stdout.decode("utf-8")

    def test_over_limit_exit1(self):
        code, out = self.run_cli("가" * 11, "--limit", "10")
        self.assertEqual(code, 1)
        self.assertIn("초과 1자", out)

    def test_ok_exit0(self):
        code, out = self.run_cli("가" * 10, "--limit", "10")
        self.assertEqual(code, 0)
        self.assertIn("남음 0자", out)

    def test_nospace_basis(self):
        code, out = self.run_cli("가 " * 10, "--limit", "10", "--basis", "nospace")
        self.assertEqual(code, 0)
        self.assertIn("공백 제외 제한 10자 중 10자", out)

    def test_cp949_file(self):
        code, out = self.run_cli("가나다", encoding="cp949")
        self.assertEqual(code, 0)
        self.assertIn("공백 포함 3자", out)

    def test_gap_warning(self):
        code, out = self.run_cli("팀원 [확인 필요: 수]명")
        self.assertIn("[확인 필요] 1곳", out)

    def test_missing_file_exit2(self):
        r = subprocess.run([sys.executable, str(SCRIPT), "없는파일.md"], capture_output=True)
        self.assertEqual(r.returncode, 2)

    def test_bad_limit_exit2(self):
        code, _ = self.run_cli("가", "--limit", "0")
        self.assertEqual(code, 2)

    def test_stdin(self):
        r = subprocess.run([sys.executable, str(SCRIPT)], input="가나".encode("utf-8"), capture_output=True)
        self.assertEqual(r.returncode, 0)
        self.assertIn("공백 포함 2자", r.stdout.decode("utf-8"))

    def test_stdin_cp949(self):
        r = subprocess.run([sys.executable, str(SCRIPT)], input="가나다".encode("cp949"), capture_output=True)
        self.assertEqual(r.returncode, 0)
        self.assertIn("공백 포함 3자", r.stdout.decode("utf-8"))

    def test_stdin_undecodable_exit2(self):
        r = subprocess.run([sys.executable, str(SCRIPT)], input=b"\xff", capture_output=True)
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
