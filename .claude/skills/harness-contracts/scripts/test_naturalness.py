import pathlib
import subprocess
import sys
import tempfile
import unittest

from naturalness_check import find_violations


SCRIPT_PATH = pathlib.Path(__file__).with_name("naturalness_check.py")


class NaturalnessCheckTests(unittest.TestCase):
    def test_accepts_plain_korean_report_copy(self):
        text = """
        검색 유입은 줄고, 브랜드 신뢰가 구매 전환의 기준이 된다.
        기업은 근거 자산을 정리하고, 고객이 확인할 수 있는 증거를 앞에 둬야 한다.
        """
        self.assertEqual(find_violations(text), [])

    def test_detects_translationese_and_overused_through_phrases(self):
        through_lines = "\n".join(f"{index}. 데이터를 통해 확인한다." for index in range(1, 10))
        text = f"""
        월요일에 시작할 실행안은 게임 체인저에 다름 아니다.
        소비자가 바뀌었다는 사실은 이미 확인되어진다.
        격차의 반대편에서 당신의 브랜드는 다시 읽히게 된다.
        {through_lines}
        """

        with tempfile.NamedTemporaryFile("w", suffix=".md", encoding="utf-8", delete=False) as handle:
            handle.write(text)
            path = pathlib.Path(handle.name)

        try:
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), str(path)],
                text=True,
                capture_output=True,
                check=False,
            )
        finally:
            path.unlink()

        self.assertEqual(result.returncode, 1)
        self.assertIn("월요일에 시작", result.stdout)
        self.assertIn("게임 체인저", result.stdout)
        self.assertIn("되어진다", result.stdout)
        self.assertIn("격차의 반대편", result.stdout)
        self.assertIn("통해_8회초과", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
