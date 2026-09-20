"""Tests for tools/repo_pulse.py — run from the repository root with:
    python3 -m unittest discover -s tests
"""
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import repo_pulse  # type: ignore[import-not-found]


class RepoPulseTests(unittest.TestCase):
    def test_collect_pulse_returns_a_dict_in_a_git_repo(self) -> None:
        pulse = repo_pulse.collect_pulse()
        self.assertIsNotNone(pulse)
        self.assertIn("branch", pulse)
        self.assertIn("head", pulse)
        self.assertIn("total_commits", pulse)
        self.assertIsInstance(pulse["total_commits"], int)

    def test_render_human_contains_the_banner(self) -> None:
        pulse = repo_pulse.collect_pulse()
        text = repo_pulse.render_human(pulse)
        self.assertIn("repo-pulse", text)
        self.assertIn("commits / 28d", text)

    def test_json_flag_emits_valid_json(self) -> None:
        result = subprocess.run(
            [sys.executable, str(TOOLS / "repo_pulse.py"), "--json"],
            capture_output=True, text=True, cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertIn("branch", data)
        self.assertIn("total_commits", data)

    def test_main_returns_one_outside_a_git_repo(self) -> None:
        # /tmp is not inside a git repo (no .git in parents, typically)
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            # Walk up to find a non-git dir; use a fresh temp dir without .git
            env = os.environ.copy()
            result = subprocess.run(
                [sys.executable, str(TOOLS / "repo_pulse.py")],
                capture_output=True, text=True, cwd=d,
            )
        self.assertEqual(result.returncode, 1)


if __name__ == "__main__":
    unittest.main()
