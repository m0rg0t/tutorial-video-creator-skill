# Troubleshooting Guide

## Video Issues

### Blank/black video in Remotion preview
**Cause:** H.265 (HEVC) codec. Browsers and Chromium (used by Remotion) cannot decode H.265.
**Fix:** Convert to H.264 with ffmpeg: `ffmpeg -i input.MOV -c:v libx264 -crf 18 -c:a aac output.mp4`

### Video appears rotated or wrong dimensions
**Cause:** iPhone videos have rotation metadata (`displaymatrix: rotation of -90.00 degrees`).
**Fix:** ffmpeg applies rotation automatically during transcoding. A 1920x1080 landscape source becomes 1080x1920 portrait. No manual rotation needed.

### Face cut off in circle overlay
**Cause:** `objectPosition` not targeting the face area.
**Fix:** Adjust `objectPosition: "center N%"` — start at 35%, preview, adjust by 5% increments. Lower % = higher in frame, higher % = lower in frame.

### Video playback out of sync
**Cause:** Variable frame rate from screen recording.
**Fix:** Re-encode with constant frame rate: `ffmpeg -i input.MOV -c:v libx264 -r 30 -crf 18 output.mp4`

## Audio Issues

### Double audio playing
**Cause:** Both `<Video>` and `<Audio>` components playing audio from the same source.
**Fix:** Add `muted` prop to all `<Video>` components. Use a single `<Audio>` component for the voiceover track.

### Audio not playing in preview
**Cause:** Browser autoplay restrictions.
**Fix:** Click the play button in Remotion studio. Audio works correctly during render.

## Transcription Issues

### Whisper API connection refused
**Cause:** Whisper server not running or wrong port.
**Fix:** Verify server is running: `curl http://localhost:12017/v1/models`

### Whisper server crashes on large files
**Cause:** Memory issues with large audio files.
**Fix:** Use smaller model (tiny-q5_1) or reduce audio quality: `ffmpeg -i input.wav -ar 16000 -ac 1 output.wav`

### No word-level timestamps from Whisper
**Cause:** Not all Whisper implementations support `timestamp_granularities[]=word`.
**Fix:** The transcription script falls back to segment-level timestamps and distributes time evenly across words. Result is approximate but visually acceptable.

### Wrong words in transcription
**Cause:** Whisper misrecognizing brand names, technical terms, or domain-specific words.
**Fix:** Manually edit `public/captions.json` after transcription. Common errors: brand names, transliterated words, technical jargon.

## Remotion Issues

### Version mismatch warning
**Cause:** Installed `remotion` and `@remotion/*` versions differ.
**Fix:** Inspect `npm ls remotion @remotion/cli @remotion/media @remotion/captions`, align all four packages to the same exact version in `package.json`, then run `npm install`. Do not add Zod unless your own components use it.

### "Cannot find module" errors
**Cause:** Missing Remotion packages.
**Fix:** Ensure all `@remotion/*` packages are the same version: `npm view remotion version`

### Render fails with "could not determine executable"
**Cause:** npm cache or node_modules corruption.
**Fix:** `rm -rf node_modules && npm install`

## Layout Issues

### Captions overlap with face circle
**Cause:** `BOTTOM_WITH_FACE` offset too small.
**Fix:** Calculate: `CIRCLE_SIZE + PADDING + border*2 + gap(~40px)`. For 400px circle: `400 + 24 + 8 + 38 = 470`

### Captions too wide or wrapping badly
**Cause:** `maxWidth` too large or text too long per page.
**Fix:** Reduce `SWITCH_CAPTIONS_EVERY_MS` (fewer words per page) or reduce `maxWidth` on the caption container.

### Screen recording not filling frame
**Cause:** Source video aspect ratio differs significantly from 9:16.
**Fix:** `objectFit: "cover"` handles this by cropping. For very wide sources, consider adding blur background: render a blurred scaled-up version behind the actual video.
