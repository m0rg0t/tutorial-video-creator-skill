#!/bin/bash
# Create the project directories and copy the dependency-free Python transcriber.
# Usage: bash scaffold.sh [target-directory]
set -euo pipefail

if [[ $# -gt 1 ]]; then
  echo "Usage: bash scaffold.sh [target-directory]" >&2
  exit 2
fi
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  echo "Usage: bash scaffold.sh [target-directory]"
  exit 0
fi

TARGET="${1:-.}"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT="$TARGET/remotion-video"
mkdir -p -- "$PROJECT/"{src/components,public,scripts,out}

# Rerunning the scaffold must not overwrite a user's configured script.
TRANSCRIBE="$PROJECT/scripts/transcribe.py"
if [[ ! -e "$TRANSCRIBE" && ! -L "$TRANSCRIBE" ]]; then
  cp -- "$SCRIPT_DIR/transcribe-template.py" "$TRANSCRIBE"
fi

printf 'Created project directories and transcription template at %s/\n\n' "$PROJECT"
echo "Next steps:"
echo "  1. Create package.json, tsconfig.json and source files from references/project-structure.md"
echo "     and the components from references/components.md"
printf '  2. cd %q && npm install\n' "$PROJECT"
echo "  3. Convert videos and extract scripts/voiceover-audio.wav using SKILL.md Step 3"
echo "  4. Configure scripts/transcribe.py, then run python3 scripts/transcribe.py"
echo "  5. npm run typecheck && npm run studio -- --port 3333"
