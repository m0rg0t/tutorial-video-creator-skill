/**
 * Whisper API Transcription Script Template
 *
 * Transcribes audio using a local OpenAI-compatible Whisper API
 * and outputs Remotion Caption[] format JSON.
 *
 * Usage: npx tsx scripts/transcribe.ts
 *
 * Configure WHISPER_API_URL and MODEL below.
 */
import fs from "fs";
import path from "path";

// === CONFIGURATION ===
const WHISPER_API_URL = "http://localhost:12017/v1/audio/transcriptions";
const MODEL = "large-v3-turbo-q5_0"; // or "tiny-q5_1" for speed
const LANGUAGE = "ru"; // Change to your language

const SCRIPT_DIR = path.dirname(new URL(import.meta.url).pathname);
const AUDIO_FILE = path.join(SCRIPT_DIR, "voiceover-audio.wav");
const OUTPUT_FILE = path.join(SCRIPT_DIR, "..", "public", "captions.json");

type WhisperWord = { word: string; start: number; end: number };
type WhisperResponse = {
  text: string;
  words?: WhisperWord[];
  segments?: Array<{
    start: number;
    end: number;
    text: string;
    words?: WhisperWord[];
  }>;
};
type Caption = {
  text: string;
  startMs: number;
  endMs: number;
  timestampMs: number | null;
  confidence: number | null;
};

async function transcribe(): Promise<void> {
  console.log("Reading audio file:", AUDIO_FILE);

  if (!fs.existsSync(AUDIO_FILE)) {
    console.error("Audio file not found! Run convert-videos.sh first.");
    process.exit(1);
  }

  const audioBuffer = fs.readFileSync(AUDIO_FILE);
  const blob = new Blob([audioBuffer], { type: "audio/wav" });

  const formData = new FormData();
  formData.append("file", blob, "voiceover-audio.wav");
  formData.append("model", MODEL);
  formData.append("response_format", "verbose_json");
  formData.append("timestamp_granularities[]", "word");
  formData.append("language", LANGUAGE);

  console.log("Sending to Whisper API at", WHISPER_API_URL, "...");

  const response = await fetch(WHISPER_API_URL, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error("Whisper API error:", response.status, errorText);
    process.exit(1);
  }

  const data: WhisperResponse = await response.json();
  console.log("Transcription:", data.text?.substring(0, 100), "...");

  // Extract words — handle both top-level and segment-level
  let words: WhisperWord[] = [];
  if (data.words && data.words.length > 0) {
    words = data.words;
  } else if (data.segments) {
    for (const segment of data.segments) {
      if (segment.words) {
        words.push(...segment.words);
      }
    }
  }

  let captions: Caption[];

  if (words.length > 0) {
    console.log(`Got ${words.length} word-level timestamps`);
    captions = words.map((w) => ({
      text: w.word,
      startMs: Math.round(w.start * 1000),
      endMs: Math.round(w.end * 1000),
      timestampMs: Math.round(w.start * 1000),
      confidence: null,
    }));
  } else if (data.segments) {
    // Fallback: distribute time evenly across words in each segment
    console.log(`Falling back to ${data.segments.length} segments`);
    captions = [];
    for (const seg of data.segments) {
      const segWords = seg.text.trim().split(/\s+/);
      const duration = seg.end - seg.start;
      const wordDur = duration / segWords.length;
      segWords.forEach((word, i) => {
        const wStart = seg.start + i * wordDur;
        const wEnd = seg.start + (i + 1) * wordDur;
        captions.push({
          text: (captions.length > 0 ? " " : "") + word,
          startMs: Math.round(wStart * 1000),
          endMs: Math.round(wEnd * 1000),
          timestampMs: Math.round(wStart * 1000),
          confidence: null,
        });
      });
    }
  } else {
    console.error("No timing data in Whisper response");
    process.exit(1);
  }

  fs.writeFileSync(OUTPUT_FILE, JSON.stringify(captions, null, 2));
  console.log(`Saved ${captions.length} captions to ${OUTPUT_FILE}`);
}

transcribe().catch((err) => {
  console.error("Transcription failed:", err);
  process.exit(1);
});
