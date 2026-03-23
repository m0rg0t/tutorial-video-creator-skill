# Tutorial Video Creator Skill

A Claude Code skill for creating polished vertical (1080x1920) tutorial videos using [Remotion](https://remotion.dev). Combines screen recordings with talking head circle overlays and TikTok-style synced captions.

## Installation

### Prerequisites

Install the Remotion best practices skill first (this skill depends on it):

```bash
npx skills add remotion-dev/skills
```

### Install this skill

```bash
npx skills add m0rg0t/tutorial-video-creator-skill
```

## Updating

```bash
# Check for available updates
npx skills check

# Update all skills to latest versions
npx skills update
```

## Uninstall

```bash
npx skills remove tutorial-video-creator
```

## What it does

This skill guides Claude through a 7-step workflow to create tutorial videos:

1. **Gather source files** — screen recording + voiceover/talking head video
2. **Scaffold Remotion project** — standalone project with proper structure
3. **Convert videos** — H.265 MOV → H.264 MP4 (browser-compatible)
4. **Transcribe audio** — extract audio, run through Whisper API, generate captions JSON
5. **Build compositions** — screen recording background + face circle + captions
6. **Preview & iterate** — adjust face crop, circle size/position, caption styling
7. **Render variants** — export multiple layout options as MP4

## Output

Three video variants are generated:

| Variant | Description |
|---------|-------------|
| CircleBottomLeft | Face circle bottom-left, captions above |
| CircleTopRight | Face circle top-right, captions at bottom |
| CaptionsOnly | No face overlay, just screen + captions + audio |

## Tech stack

- **[Remotion](https://remotion.dev)** — React-based video composition
- **FFmpeg** — Video conversion (H.265 → H.264)
- **Whisper API** — Audio transcription with word-level timestamps
- **@remotion/captions** — TikTok-style caption rendering

## Trigger phrases

The skill activates when you ask Claude to:
- "Create a tutorial video"
- "Make an educational video"
- "Combine screen recording with voiceover"
- "Add face circle overlay to video"
- "Create vertical video with captions"
- "Make a Remotion video"
- "Add subtitles to screen recording"

## License

MIT
