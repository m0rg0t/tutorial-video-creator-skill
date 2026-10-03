# Project Structure Reference

## Directory Layout

```
remotion-video/
├── package.json
├── tsconfig.json
├── remotion.config.ts
├── src/
│   ├── index.ts                    # registerRoot entry point
│   ├── Root.tsx                    # Composition definitions
│   ├── TutorialVideo.tsx           # Main composition component
│   ├── components/
│   │   ├── ScreenRecording.tsx     # Background screen recording
│   │   ├── FaceCircle.tsx          # Circular face overlay
│   │   └── Captions.tsx            # TikTok-style captions
│   └── types.ts                    # Shared TypeScript types
├── public/                         # Converted assets + captions
│   ├── screen-recording.mp4
│   ├── voiceover.mp4
│   ├── voiceover-audio.wav         # Optional enhanced audio
│   └── captions.json
├── scripts/
│   └── transcribe.py               # Copied by scaffold.sh
└── out/                            # Rendered output
```

## package.json

```json
{
  "name": "tutorial-video",
  "version": "1.0.0",
  "private": true,
  "engines": {
    "node": ">=24"
  },
  "scripts": {
    "studio": "remotion studio",
    "render:all": "npm run render:v1 && npm run render:v2 && npm run render:v3",
    "render:v1": "remotion render CircleBottomLeft out/circle-bottom-left.mp4",
    "render:v2": "remotion render CircleTopRight out/circle-top-right.mp4",
    "render:v3": "remotion render CaptionsOnly out/captions-only.mp4",
    "typecheck": "tsc --noEmit",
    "transcribe": "python3 scripts/transcribe.py"
  },
  "dependencies": {
    "@remotion/cli": "4.0.532",
    "@remotion/media": "4.0.532",
    "@remotion/captions": "4.0.532",
    "react": "19.3.0",
    "react-dom": "19.3.0",
    "remotion": "4.0.532"
  },
  "devDependencies": {
    "@types/react": "19.3.0",
    "typescript": "7.0.2"
  }
}
```

Use Node.js 24 LTS, Python 3.11+ and FFmpeg. The scripts require no Python packages. The direct npm versions above were checked on 2026-10-03; commit the generated `package-lock.json` in your video project and use `npm ci` for repeat installs. `tsx`, Zod and an ESLint config are not needed by these templates.

**Important:** All `@remotion/*` and `remotion` packages must share the exact same version. Check latest with `npm view remotion version`.

## tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ES2022",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true
  },
  "include": ["src/**/*.ts", "src/**/*.tsx", "remotion.config.ts"]
}
```

## remotion.config.ts

```ts
import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
```

## src/index.ts

```ts
import { registerRoot } from "remotion";
import { RemotionRoot } from "./Root";

registerRoot(RemotionRoot);
```

## src/types.ts

```ts
export type FacePosition = "bottom-left" | "top-right" | "none";
export type CaptionsPosition = "top" | "bottom";

export type TutorialVideoProps = {
  facePosition: FacePosition;
  captionsPosition: CaptionsPosition;
};
```

## src/Root.tsx

```tsx
import { Composition } from "remotion";
import { TutorialVideo } from "./TutorialVideo";
import type { TutorialVideoProps } from "./types";

const FPS = 30;
const DURATION_SECONDS = 29; // Adjust to match source video length
const DURATION_FRAMES = DURATION_SECONDS * FPS;
const WIDTH = 1080;
const HEIGHT = 1920;

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="CircleBottomLeft"
        component={TutorialVideo}
        durationInFrames={DURATION_FRAMES}
        fps={FPS}
        width={WIDTH}
        height={HEIGHT}
        defaultProps={{
          facePosition: "bottom-left",
          captionsPosition: "bottom",
        } satisfies TutorialVideoProps}
      />
      <Composition
        id="CircleTopRight"
        component={TutorialVideo}
        durationInFrames={DURATION_FRAMES}
        fps={FPS}
        width={WIDTH}
        height={HEIGHT}
        defaultProps={{
          facePosition: "top-right",
          captionsPosition: "bottom",
        } satisfies TutorialVideoProps}
      />
      <Composition
        id="CaptionsOnly"
        component={TutorialVideo}
        durationInFrames={DURATION_FRAMES}
        fps={FPS}
        width={WIDTH}
        height={HEIGHT}
        defaultProps={{
          facePosition: "none",
          captionsPosition: "bottom",
        } satisfies TutorialVideoProps}
      />
    </>
  );
};
```

## src/TutorialVideo.tsx

```tsx
import { Audio } from "@remotion/media";
import { AbsoluteFill, staticFile } from "remotion";
import { ScreenRecording } from "./components/ScreenRecording";
import { FaceCircle } from "./components/FaceCircle";
import { Captions } from "./components/Captions";
import type { TutorialVideoProps } from "./types";

export const TutorialVideo: React.FC<TutorialVideoProps> = ({
  facePosition,
  captionsPosition,
}) => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      <ScreenRecording />
      <Audio src={staticFile("voiceover-audio.wav")} />
      {facePosition !== "none" && <FaceCircle position={facePosition} />}
      <Captions position={captionsPosition} facePosition={facePosition} />
    </AbsoluteFill>
  );
};
```

## Captions JSON Format

The `public/captions.json` file must follow the Remotion `Caption` type:

```json
[
  {
    "text": "Первое",
    "startMs": 1100,
    "endMs": 1500,
    "timestampMs": 1100,
    "confidence": null
  },
  {
    "text": " слово",
    "startMs": 1500,
    "endMs": 1900,
    "timestampMs": 1500,
    "confidence": null
  }
]
```

**Note:** Words after the first should have a leading space in `text` for proper `whiteSpace: "pre"` rendering. When using flex-wrap layout with `.trim()`, spaces are optional.
