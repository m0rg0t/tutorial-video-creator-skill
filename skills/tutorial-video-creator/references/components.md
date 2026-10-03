# Component Reference

Detailed implementations of the three core components for tutorial video composition.

## ScreenRecording.tsx

Full-screen background layer displaying the screen recording, scaled to fill the vertical frame.

```tsx
import { Video } from "@remotion/media";
import { AbsoluteFill, staticFile } from "remotion";

export const ScreenRecording: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      <Video
        src={staticFile("screen-recording.mp4")}
        muted
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
        }}
      />
    </AbsoluteFill>
  );
};
```

**Notes:**
- Always `muted` — audio comes from separate `<Audio>` component
- `objectFit: "cover"` scales to fill the 1080x1920 frame, cropping excess
- Black background shows during any gaps or aspect ratio mismatch

## FaceCircle.tsx

Circular overlay showing the talking head video. Configurable size and position.

```tsx
import { Video } from "@remotion/media";
import {
  AbsoluteFill,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { FacePosition } from "../types";

const CIRCLE_SIZE = 400;
const PADDING = 24;

const positionStyles: Record<
  Exclude<FacePosition, "none">,
  React.CSSProperties
> = {
  "bottom-left": {
    bottom: PADDING,
    left: PADDING,
  },
  "top-right": {
    top: PADDING,
    right: PADDING,
  },
};

export const FaceCircle: React.FC<{
  position: Exclude<FacePosition, "none">;
}> = ({ position }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entrance = spring({
    frame,
    fps,
    config: { damping: 200 },
  });

  const scale = interpolate(entrance, [0, 1], [0.5, 1]);
  const opacity = entrance;

  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          ...positionStyles[position],
          width: CIRCLE_SIZE,
          height: CIRCLE_SIZE,
          borderRadius: "50%",
          overflow: "hidden",
          border: "4px solid white",
          boxShadow: "0 4px 20px rgba(0, 0, 0, 0.4)",
          transform: `scale(${scale})`,
          opacity,
        }}
      >
        <Video
          src={staticFile("voiceover.mp4")}
          muted
          style={{
            position: "absolute",
            width: CIRCLE_SIZE,
            height: CIRCLE_SIZE,
            objectFit: "cover",
            objectPosition: "center 35%",
            top: 0,
            left: 0,
          }}
        />
      </div>
    </AbsoluteFill>
  );
};
```

### Face Cropping Guide

The `objectPosition` percentage controls which part of the source video fills the circle:

| Value | Effect | Use when |
|-------|--------|----------|
| `center 25%` | Shows very top of frame | Face is high in frame |
| `center 35%` | Upper third focus | Typical iPhone front camera |
| `center 44%` | Slightly above center | Face is centered in frame |
| `center 50%` | Exact center | Face is dead center |

**How it works:** The `<Video>` element is set to the same width and height as the circle (square). `objectFit: "cover"` makes the video content fill this square, cropping the excess. `objectPosition` controls the anchor point for the crop.

**Iteration workflow:** Start at 35%, preview in Remotion studio, adjust up/down by 5% increments until the face is well-framed in the circle.

### Size Guide

| CIRCLE_SIZE | Visual Effect |
|-------------|---------------|
| 200 | Small, unobtrusive — good for detailed screen recordings |
| 300 | Medium, balanced presence |
| 400 | Large, prominent — good for tutorial/educational feel |

## Captions.tsx

TikTok-style word-by-word captions with active word highlighting.

```tsx
import { useState, useEffect, useCallback, useMemo } from "react";
import {
  AbsoluteFill,
  Sequence,
  staticFile,
  useCurrentFrame,
  useDelayRender,
  useVideoConfig,
} from "remotion";
import {
  createTikTokStyleCaptions,
  type Caption,
  type TikTokPage,
} from "@remotion/captions";
import type { CaptionsPosition, FacePosition } from "../types";

const SWITCH_CAPTIONS_EVERY_MS = 1500;
const HIGHLIGHT_COLOR = "#FFDD00";
const FONT_SIZE = 52;

// Face circle clearance: CIRCLE_SIZE + PADDING + border + gap
const BOTTOM_WITH_FACE = 470;
const BOTTOM_WITHOUT_FACE = 180;

const CaptionPage: React.FC<{ page: TikTokPage }> = ({ page }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const currentTimeMs = (frame / fps) * 1000;
  const absoluteTimeMs = page.startMs + currentTimeMs;

  return (
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "center",
        gap: 6,
        maxWidth: 900,
      }}
    >
      {page.tokens.map((token) => {
        const isActive =
          token.fromMs <= absoluteTimeMs && token.toMs > absoluteTimeMs;

        return (
          <span
            key={token.fromMs}
            style={{
              fontSize: FONT_SIZE,
              fontWeight: 900,
              fontFamily:
                '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
              color: isActive ? "#000" : "#fff",
              backgroundColor: isActive
                ? HIGHLIGHT_COLOR
                : "rgba(0, 0, 0, 0.65)",
              borderRadius: 10,
              padding: "4px 12px",
              lineHeight: 1.2,
              letterSpacing: "-0.02em",
            }}
          >
            {token.text.trim()}
          </span>
        );
      })}
    </div>
  );
};

export const Captions: React.FC<{
  position: CaptionsPosition;
  facePosition: FacePosition;
}> = ({ position, facePosition }) => {
  const hasBottomFace =
    facePosition === "bottom-left" && position === "bottom";
  const [captions, setCaptions] = useState<Caption[] | null>(null);
  const { delayRender, continueRender, cancelRender } = useDelayRender();
  const [handle] = useState(() => delayRender("Loading captions.json"));
  const { fps } = useVideoConfig();

  const fetchCaptions = useCallback(async () => {
    try {
      const response = await fetch(staticFile("captions.json"));
      if (!response.ok) {
        throw new Error(`Failed to load captions: HTTP ${response.status}`);
      }
      const data: unknown = await response.json();
      if (!Array.isArray(data)) {
        throw new Error("captions.json must contain a Caption[] array");
      }
      setCaptions(data as Caption[]);
      continueRender(handle);
    } catch (error) {
      cancelRender(error);
    }
  }, [handle, continueRender, cancelRender]);

  useEffect(() => {
    fetchCaptions();
  }, [fetchCaptions]);

  const pages = useMemo(() => {
    if (!captions) return [];
    const result = createTikTokStyleCaptions({
      captions,
      combineTokensWithinMilliseconds: SWITCH_CAPTIONS_EVERY_MS,
    });
    return result.pages;
  }, [captions]);

  if (!captions || pages.length === 0) {
    return null;
  }

  return (
    <AbsoluteFill>
      {pages.map((page, index) => {
        const nextPage = pages[index + 1] ?? null;
        const startFrame = (page.startMs / 1000) * fps;
        const endFrame = Math.min(
          nextPage ? (nextPage.startMs / 1000) * fps : Infinity,
          startFrame + (SWITCH_CAPTIONS_EVERY_MS / 1000) * fps,
        );
        const durationInFrames = Math.max(
          1,
          Math.round(endFrame - startFrame),
        );

        return (
          <Sequence
            key={index}
            from={Math.round(startFrame)}
            durationInFrames={durationInFrames}
            layout="none"
          >
            <div
              style={{
                position: "absolute",
                left: 40,
                right: 40,
                display: "flex",
                justifyContent: "center",
                ...(position === "top"
                  ? { top: 160 }
                  : {
                      bottom: hasBottomFace
                        ? BOTTOM_WITH_FACE
                        : BOTTOM_WITHOUT_FACE,
                    }),
              }}
            >
              <CaptionPage page={page} />
            </div>
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
```

The render is delayed until `captions.json` loads successfully; HTTP and parsing errors cancel the render instead of silently producing a video without captions. See [Remotion data fetching](https://www.remotion.dev/docs/data-fetching) and [useDelayRender](https://www.remotion.dev/docs/use-delay-render).

### Caption Styling Options

| Parameter | Default | Effect |
|-----------|---------|--------|
| `SWITCH_CAPTIONS_EVERY_MS` | 1500 | How often caption pages switch. Lower = fewer words per page |
| `HIGHLIGHT_COLOR` | `#FFDD00` | Active word background color |
| `FONT_SIZE` | 52 | Caption text size in pixels |
| `BOTTOM_WITH_FACE` | 470 | Bottom offset when face circle is present |
| `BOTTOM_WITHOUT_FACE` | 180 | Bottom offset without face circle |

### Caption-Face Overlap Prevention

Calculate `BOTTOM_WITH_FACE` as: `CIRCLE_SIZE + PADDING + border_width*2 + gap`

Example: `400 + 24 + 8 + 38 = 470`
