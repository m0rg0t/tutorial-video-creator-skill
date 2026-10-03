---
name: Tutorial Video Creator
description: This skill should be used when the user asks to "create a tutorial video", "make an educational video", "combine screen recording with voiceover", "add face circle overlay to video", "create vertical video with captions", "make a Remotion video", "add subtitles to screen recording", or needs to produce vertical social media videos from screen recordings and talking head footage.
version: 0.1.1
---

# Tutorial Video Creator

Create polished vertical (1080x1920) tutorial videos by compositing a screen recording with a talking head circle overlay and synced TikTok-style captions using Remotion.

## Prerequisites

This skill depends on the **remotion-best-practices** skill for Remotion-specific patterns and API knowledge. Install it first:

```bash
npx skills add remotion-dev/skills
```

When working on Remotion compositions, also load the remotion-best-practices skill for detailed rules on animations, timing, videos, and audio components.

## Workflow Overview

1. **Gather source files** — screen recording + voiceover/talking head video
2. **Scaffold Remotion project** — standalone project with proper structure
3. **Convert videos** — H.265 MOV → H.264 MP4 (browser-compatible)
4. **Transcribe audio** — extract audio, run through Whisper API, generate captions JSON
5. **Build compositions** — screen recording background + face circle + captions
6. **Preview & iterate** — adjust face crop, circle size/position, caption styling
7. **Render variants** — export multiple layout options as MP4

## Step 1: Gather Source Files

Collect from the user:
- **Screen recording** (any format, typically MOV from iPhone/macOS)
- **Voiceover video** (talking head with audio) OR separate audio file
- Desired output format (vertical 1080x1920 for Reels/Stories/TikTok is default)

## Step 2: Scaffold Remotion Project

Use Node.js 24 LTS, Python 3.11+ and FFmpeg. From this skill directory, create the project directories and copy the Python transcription template:

```bash
bash scripts/scaffold.sh <target-directory>
```

Then create the source files from **`references/project-structure.md`** and **`references/components.md`** before installing dependencies (the scaffold does not generate these files):

```bash
cd <target-directory>/remotion-video && npm install
```

For the full project structure and component code, consult **`references/project-structure.md`**.

## Step 3: Convert Videos with FFmpeg

H.265 (HEVC) videos from iPhones **cannot be decoded by browsers**. Convert to H.264:

```bash
# Screen recording → H.264
ffmpeg -i source-screen.MOV -c:v libx264 -crf 18 -c:a aac -y public/screen-recording.mp4

# Voiceover → H.264
ffmpeg -i source-voiceover.MOV -c:v libx264 -crf 18 -c:a aac -y public/voiceover.mp4

# Extract audio for transcription (16kHz mono WAV for Whisper)
ffmpeg -i source-voiceover.MOV -ar 16000 -ac 1 -f wav scripts/voiceover-audio.wav

# Extract high-quality audio for enhancement (48kHz stereo)
ffmpeg -i source-voiceover.MOV -vn -c:a pcm_s16le -ar 48000 public/voiceover-audio.wav
```

**Key gotcha:** iPhone portrait videos store rotation as metadata (`displaymatrix: rotation of -90.00 degrees`). FFmpeg applies this automatically during transcoding — a 1920x1080 landscape source becomes 1080x1920 portrait output.

## Step 4: Transcribe Audio

Use the transcription script with local Whisper API:

```bash
python3 scripts/transcribe.py
```

Configure the Whisper API URL and model in the script. Default: `http://localhost:12017`.

If only segment-level timestamps are returned (no word-level), the script distributes time evenly across words within each segment — approximate but visually acceptable.

**Post-transcription:** Review `public/captions.json` for recognition errors. Common fixes for Russian: brand names, technical terms (промпт vs промпут), proper nouns.

## Step 5: Build Compositions

The project creates multiple variants with configurable props. For component implementation details, consult **`references/components.md`**.

### Key Component Patterns

**Face Circle** — circular crop of talking head video overlaid on screen recording:
- `objectFit: "cover"` + `objectPosition: "center N%"` on a square `<Video>` element
- Adjust N% to center the face (typically 30-45% for iPhone front camera)
- Spring entrance animation for polish
- White border + box-shadow for visibility

**Captions** — TikTok-style word-by-word highlighting:
- `createTikTokStyleCaptions()` from `@remotion/captions`
- Active word: yellow background + black text; inactive: dark semi-transparent bg + white text
- Position must account for face circle to avoid overlap

**Audio** — can use either video file or separate enhanced audio:
- `<Audio src={staticFile("voiceover-audio.wav")} />` for enhanced audio
- Mute the face `<Video>` to avoid double audio

### Variant Composition Table

| Variant | Face Position | Captions Position |
|---------|--------------|-------------------|
| CircleBottomLeft | bottom-left | bottom (raised above circle) |
| CircleTopRight | top-right | bottom |
| CaptionsOnly | none | bottom |

## Step 6: Preview & Iterate

```bash
npx remotion studio --port 3333
```

Common adjustments during preview:
- **Face not centered in circle** → adjust `objectPosition` percentage
- **Circle too small/large** → change `CIRCLE_SIZE` constant
- **Captions overlap face** → increase `BOTTOM_WITH_FACE` offset
- **Caption text errors** → edit `public/captions.json` directly

Extract frames for quick visual checks without the studio:
```bash
ffmpeg -i public/screen-recording.mp4 -vf "fps=2,scale=296:-1" out/frames/frame_%03d.jpg
```

## Step 7: Render

```bash
# Single variant
npx remotion render CircleBottomLeft out/circle-bottom-left.mp4

# All variants
npm run render:all
```

## Additional Resources

### Reference Files
- **`references/project-structure.md`** — Full project scaffold, package.json, tsconfig, component code
- **`references/components.md`** — Detailed component implementations (FaceCircle, Captions, ScreenRecording)
- **`references/troubleshooting.md`** — Common issues and solutions

### Scripts
- **`scripts/scaffold.sh`** — Creates project directories and copies `scripts/transcribe.py` without overwriting an existing copy
- **`scripts/transcribe-template.py`** — Whisper API transcription script (Python 3, no dependencies)
