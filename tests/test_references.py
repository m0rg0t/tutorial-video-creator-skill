import json
from pathlib import Path
import tempfile
import unittest

from materialize_reference import materialize, reference_files


class ReferenceTests(unittest.TestCase):
    def test_exact_documented_project_is_extracted(self):
        files = reference_files()
        self.assertEqual(len(files), 10)
        self.assertIn("src/components/Captions.tsx", files)
        for name in ("package.json", "tsconfig.json"):
            json.loads(files[name])

    def test_package_versions_match_and_python_replaces_tsx(self):
        package = json.loads(reference_files()["package.json"])
        versions = {version for name, version in package["dependencies"].items()
                    if name == "remotion" or name.startswith("@remotion/")}
        self.assertEqual(len(versions), 1)
        self.assertRegex(versions.pop(), r"^\d+\.\d+\.\d+$")
        self.assertEqual(package["dependencies"]["react"], package["dependencies"]["react-dom"])
        self.assertEqual(package["scripts"]["transcribe"], "python3 scripts/transcribe.py")
        self.assertNotIn("tsx", package["devDependencies"])
        self.assertNotIn("zod", package["dependencies"])
        self.assertIn("remotion.config.ts", json.loads(reference_files()["tsconfig.json"])["include"])

    def test_materialize_without_overwriting_existing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "reference"
            materialize(destination)
            self.assertEqual((destination / "package.json").read_text(),
                             reference_files()["package.json"])
            with self.assertRaises(ValueError):
                materialize(destination)


if __name__ == "__main__":
    unittest.main()
