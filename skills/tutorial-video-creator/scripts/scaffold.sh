#!/bin/bash
# Scaffold a Remotion tutorial video project
# Usage: bash scaffold.sh <target-directory>

set -e

TARGET="${1:-.}"

if [ "$TARGET" != "." ]; then
  mkdir -p "$TARGET"
fi

mkdir -p "$TARGET/remotion-video/"{src/components,public,scripts,out}

echo "Scaffolded Remotion tutorial video project at $TARGET/remotion-video/"
echo ""
echo "Next steps:"
echo "  1. Copy source videos to the parent directory"
echo "  2. cd $TARGET/remotion-video && npm install"
echo "  3. bash scripts/convert-videos.sh"
echo "  4. npx tsx scripts/transcribe.ts"
echo "  5. npx remotion studio --port 3333"
echo ""
echo "Create the source files (package.json, tsconfig.json, etc.) using the"
echo "project-structure.md reference, or let Claude generate them."
