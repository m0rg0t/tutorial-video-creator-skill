#!/usr/bin/env python3
"""
Whisper API Transcription Script Template

Transcribes audio using a local OpenAI-compatible Whisper API
and outputs Remotion Caption[] format JSON.

Usage: python3 scripts/transcribe.py

No dependencies beyond Python 3 standard library.
"""
import json
import os
import sys
import urllib.request
import urllib.error

# === CONFIGURATION ===
WHISPER_API_URL = "http://localhost:12017/v1/audio/transcriptions"
MODEL = "large-v3-turbo-q5_0"  # or "tiny-q5_1" for speed
LANGUAGE = "ru"  # Change to your language

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_FILE = os.path.join(SCRIPT_DIR, "voiceover-audio.wav")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "..", "public", "captions.json")


def build_multipart(fields, files):
    """Build multipart/form-data body without external dependencies."""
    boundary = "----PythonFormBoundary7MA4YWxkTrZu0gW"
    body = b""
    for key, value in fields.items():
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode()
        body += f"{value}\r\n".encode()
    for key, (filename, data, content_type) in files.items():
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="{key}"; filename="{filename}"\r\n'.encode()
        body += f"Content-Type: {content_type}\r\n\r\n".encode()
        body += data + b"\r\n"
    body += f"--{boundary}--\r\n".encode()
    return body, f"multipart/form-data; boundary={boundary}"


def transcribe():
    print(f"Reading audio file: {AUDIO_FILE}")
    if not os.path.exists(AUDIO_FILE):
        print("Audio file not found! Run convert-videos.sh first.", file=sys.stderr)
        sys.exit(1)

    with open(AUDIO_FILE, "rb") as f:
        audio_data = f.read()

    fields = {
        "model": MODEL,
        "response_format": "verbose_json",
        "timestamp_granularities[]": "word",
        "language": LANGUAGE,
    }
    files = {
        "file": ("voiceover-audio.wav", audio_data, "audio/wav"),
    }

    body, content_type = build_multipart(fields, files)

    print(f"Sending to Whisper API at {WHISPER_API_URL} ...")
    req = urllib.request.Request(
        WHISPER_API_URL,
        data=body,
        headers={"Content-Type": content_type},
    )

    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Whisper API error: {e.code} {e.read().decode()}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Connection failed: {e.reason}", file=sys.stderr)
        sys.exit(1)

    print(f"Transcription: {data.get('text', '')[:100]} ...")

    # Extract word-level timestamps if available
    words = data.get("words", [])
    if not words:
        for seg in data.get("segments", []):
            words.extend(seg.get("words", []))

    captions = []

    if words:
        print(f"Got {len(words)} word-level timestamps")
        for w in words:
            captions.append({
                "text": w["word"],
                "startMs": round(w["start"] * 1000),
                "endMs": round(w["end"] * 1000),
                "timestampMs": round(w["start"] * 1000),
                "confidence": None,
            })
    elif data.get("segments"):
        # Fallback: distribute time evenly across words in each segment
        segments = data["segments"]
        print(f"Falling back to {len(segments)} segments")
        for seg in segments:
            seg_words = seg["text"].strip().split()
            duration = seg["end"] - seg["start"]
            word_dur = duration / len(seg_words) if seg_words else duration
            for i, word in enumerate(seg_words):
                w_start = seg["start"] + i * word_dur
                w_end = seg["start"] + (i + 1) * word_dur
                prefix = " " if captions else ""
                captions.append({
                    "text": prefix + word,
                    "startMs": round(w_start * 1000),
                    "endMs": round(w_end * 1000),
                    "timestampMs": round(w_start * 1000),
                    "confidence": None,
                })
    else:
        print("No timing data in Whisper response", file=sys.stderr)
        sys.exit(1)

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(captions, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(captions)} captions to {OUTPUT_FILE}")


if __name__ == "__main__":
    transcribe()
