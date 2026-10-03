from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/tutorial-video-creator/scripts"


class ScaffoldTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def run_scaffold(self, *arguments):
        return subprocess.run(
            ["bash", str(SCRIPTS / "scaffold.sh"), *arguments], cwd=self.root,
            capture_output=True, text=True, check=False,
        )

    def test_default_target_and_transcriber_copy(self):
        result = self.run_scaffold()
        self.assertEqual(result.returncode, 0, result.stderr)
        project = self.root / "remotion-video"
        for directory in ("src/components", "public", "scripts", "out"):
            self.assertTrue((project / directory).is_dir())
        self.assertEqual((project / "scripts/transcribe.py").read_bytes(),
                         (SCRIPTS / "transcribe-template.py").read_bytes())
        self.assertIn("python3 scripts/transcribe.py", result.stdout)
        self.assertNotIn("transcribe.ts", result.stdout)
        self.assertNotIn("convert-videos.sh", result.stdout)

    def test_paths_with_spaces_unicode_and_leading_hyphen(self):
        for target in ("video with spaces", "видео", "-project"):
            with self.subTest(target=target):
                result = self.run_scaffold(target)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue((self.root / target / "remotion-video/scripts/transcribe.py").is_file())

    def test_rerun_preserves_configured_script_and_assets(self):
        self.assertEqual(self.run_scaffold().returncode, 0)
        project = self.root / "remotion-video"
        script = project / "scripts/transcribe.py"
        script.write_text("# user configuration\n")
        asset = project / "public/captions.json"
        asset.write_text("[]")
        self.assertEqual(self.run_scaffold().returncode, 0)
        self.assertEqual(script.read_text(), "# user configuration\n")
        self.assertEqual(asset.read_text(), "[]")

    def test_dangling_transcriber_symlink_is_not_overwritten(self):
        scripts = self.root / "remotion-video/scripts"
        scripts.mkdir(parents=True)
        destination = scripts / "transcribe.py"
        destination.symlink_to(self.root / "missing-script.py")
        self.assertEqual(self.run_scaffold().returncode, 0)
        self.assertTrue(destination.is_symlink())
        self.assertFalse((self.root / "missing-script.py").exists())

    def test_usage_and_help(self):
        self.assertEqual(self.run_scaffold("one", "two").returncode, 2)
        self.assertEqual(self.run_scaffold("--help").returncode, 0)
        self.assertEqual(list(self.root.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
