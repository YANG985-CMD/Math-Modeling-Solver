from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPECIALISTS = (
    "audit-modeling-evidence",
    "build-modeling-figures",
    "deliver-cumcm-paper",
)


class SkillPackTests(unittest.TestCase):
    def test_specialists_have_valid_discovery_metadata(self) -> None:
        for name in SPECIALISTS:
            with self.subTest(skill=name):
                skill = (ROOT / name / "SKILL.md").read_text(encoding="utf-8")
                self.assertNotIn("TODO", skill)
                match = re.match(r"---\n(.*?)\n---\n", skill, flags=re.DOTALL)
                self.assertIsNotNone(match)
                frontmatter = match.group(1)
                self.assertIn(f"name: {name}", frontmatter)
                self.assertRegex(frontmatter, r"(?m)^description: .+Use when .+$")

                metadata = (ROOT / name / "agents" / "openai.yaml").read_text(
                    encoding="utf-8"
                )
                self.assertIn(f"${name}", metadata)

    def test_root_skill_routes_narrow_requests(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for name in SPECIALISTS:
            self.assertIn(name, skill)
        self.assertIn("workflow_stage", skill)
        self.assertIn("result_status", skill)
        self.assertNotIn("exploratory → candidate", skill)

    def test_specialist_resources_are_synchronized(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/sync_specialist_skills.py", "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_installer_creates_four_discoverable_skills(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "skills"
            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/install_skill_pack.py",
                    "--target",
                    str(target),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            for name in ("math-modeling-solver", *SPECIALISTS):
                with self.subTest(skill=name):
                    self.assertTrue((target / name / "SKILL.md").is_file())
                    self.assertTrue((target / name / "agents" / "openai.yaml").is_file())


if __name__ == "__main__":
    unittest.main()
