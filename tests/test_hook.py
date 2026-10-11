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

    def test_broken_settings_is_absent(self):
        self.assertFalse(H.jasoseo_active(home(INSTALLED, "{broken")))

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

    def test_dev_prompts_not_prose(self):
        for p in ["버그 리포트 작성해줘", "테스트 커버리지 리포트 생성해줘", "에러 리포트 정리해줘",
                  "이번 과제 코드 수정해줘", "과제 목록 정리해줘"]:
            self.assertIsNone(self.kind(p), p)

    def test_academic_task_prose(self):
        self.assertEqual(self.kind("수업 과제 글 써줘"), "prose")
        self.assertEqual(self.kind("과제물 다듬어줘"), "prose")

    def test_strong_prose_beats_formal_reference(self):
        self.assertEqual(self.kind("보고서를 참고해서 블로그 글 써줘"), "prose")
        self.assertEqual(self.kind("보고서를 문단 글로 다듬어줘"), "prose")

    def test_data_column_not_prose(self):
        self.assertIsNone(self.kind("이 CSV의 칼럼 이름 수정해줘"))
        self.assertEqual(self.kind("신문 칼럼 써줘"), "prose")

    def test_data_column_with_particle_not_prose(self):
        for p in ["칼럼을 추가해서 표 수정해줘", "DB 칼럼을 정리해줘"]:
            self.assertIsNone(self.kind(p, jasoseo=False), p)

    def test_work_reports_with_word_between_not_prose(self):
        for p in ["테스트 결과 리포트 작성해줘", "버그 분석 리포트 써줘", "장애 분석 리포트 초안 써줘",
                  "QA 리포트 정리해줘", "주간 리포트 작성해줘", "매출 분석 리포트 써줘"]:
            self.assertNotEqual(self.kind(p), "prose", p)
        self.assertEqual(self.kind("교양 수업 리포트 써줘"), "prose")

    def test_non_dict_stdin_does_not_crash(self):
        for raw in [b"[1,2]", b'"x"']:
            r = subprocess.run([sys.executable, str(HOOK)], input=raw, capture_output=True)
            self.assertEqual(r.returncode, 0, raw)

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
