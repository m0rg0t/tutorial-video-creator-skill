"""Extract only the documented project files for offline inspection/type checking."""
import argparse
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
REFERENCES = ROOT / "skills/tutorial-video-creator/references"
PROJECT_FILES = {
    "package.json", "tsconfig.json", "remotion.config.ts", "src/index.ts",
    "src/types.ts", "src/Root.tsx", "src/TutorialVideo.tsx",
}
COMPONENT_FILES = {"ScreenRecording.tsx", "FaceCircle.tsx", "Captions.tsx"}


def reference_files():
    files = {}
    for name, expected, prefix in (
        ("project-structure.md", PROJECT_FILES, ""),
        ("components.md", COMPONENT_FILES, "src/components/"),
    ):
        text = (REFERENCES / name).read_text(encoding="utf-8")
        sections = re.split(r"^## (.+)$", text, flags=re.MULTILINE)
        for heading, body in zip(sections[1::2], sections[2::2]):
            if heading not in expected:
                continue
            match = re.search(r"^```(?:json|tsx|ts)\n(.*?)^```", body,
                              flags=re.MULTILINE | re.DOTALL)
            if match is None:
                raise ValueError(f"Missing code block for {heading}")
            files[prefix + heading] = match.group(1)
        if {prefix + path for path in expected} - files.keys():
            raise ValueError(f"Missing documented files in {name}")
    return files


def materialize(destination):
    destination = Path(destination)
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("Reference project destination must be empty")
    for name, content in reference_files().items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    materialize(args.destination)
