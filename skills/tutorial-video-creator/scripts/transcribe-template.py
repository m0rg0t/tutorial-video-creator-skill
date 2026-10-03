#!/usr/bin/env python3
"""Transcribe local audio to Remotion Caption[] using only Python's standard library.

Copy to scripts/transcribe.py, configure the constants, then run with Python 3.11+.
"""
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import urllib.error
import urllib.request
import uuid

# === CONFIGURATION ===
WHISPER_API_URL = "http://localhost:12017/v1/audio/transcriptions"
MODEL = "large-v3-turbo-q5_0"  # Must be a model supported by your local server.
LANGUAGE = "ru"  # Change to your language.

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_FILE = os.path.join(SCRIPT_DIR, "voiceover-audio.wav")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "..", "public", "captions.json")


def build_multipart(fields, files):
    """Build a multipart body with a fresh boundary for each request."""
    boundary = "----PythonFormBoundary" + uuid.uuid4().hex
    parts = []
    for key, value in fields.items():
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"'
            f"\r\n\r\n{value}\r\n".encode()
        )
    for key, (filename, data, content_type) in files.items():
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"; '
            f'filename="{filename}"\r\nContent-Type: {content_type}\r\n\r\n'.encode()
        )
        parts.extend((data, b"\r\n"))
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def _time_range(item):
    start, end = item.get("start"), item.get("end")
    for value in (start, end):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
        ):
            raise ValueError("Timestamps must be finite, non-negative numbers")
    if end < start:
        raise ValueError("A timestamp ends before it starts")
    return start, end


def captions_from_response(data):
    """Convert word timestamps or per-segment fallbacks without losing segments."""
    if not isinstance(data, dict):
        raise ValueError("Whisper response must be a JSON object")
    captions = []

    def append(text, start, end):
        if not isinstance(text, str):
            raise ValueError("Caption text must be a string")
        text = text.strip()
        if text:
            captions.append({
                "text": (" " if captions else "") + text,
                "startMs": round(start * 1000),
                "endMs": round(end * 1000),
                "timestampMs": round(start * 1000),
                "confidence": None,
            })

    def append_words(words):
        if not isinstance(words, list):
            raise ValueError("Word timestamps must be a list")
        for word in words:
            if not isinstance(word, dict):
                raise ValueError("Each word timestamp must be an object")
            start, end = _time_range(word)
            append(word.get("word"), start, end)

    words = data.get("words")
    if words:
        append_words(words)
    else:
        segments = data.get("segments") or []
        if not isinstance(segments, list):
            raise ValueError("Segments must be a list")
        for segment in segments:
            if not isinstance(segment, dict):
                raise ValueError("Each segment must be an object")
            if segment.get("words"):
                append_words(segment["words"])
                continue
            text = segment.get("text")
            if not isinstance(text, str):
                raise ValueError("Segment text must be a string")
            segment_words = text.split()
            if not segment_words:
                continue
            start, end = _time_range(segment)
            duration = (end - start) / len(segment_words)
            for index, word in enumerate(segment_words):
                append(word, start + index * duration, start + (index + 1) * duration)

    if not captions:
        raise ValueError("No usable timing data in Whisper response")
    return captions


def write_captions(captions, output_file):
    """Replace output only after a complete JSON file has been written."""
    output = Path(output_file)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=output.parent,
            prefix=f".{output.name}.", suffix=".tmp", delete=False,
        ) as stream:
            temporary = Path(stream.name)
            json.dump(captions, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
        os.replace(temporary, output)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def transcribe():
    print(f"Reading audio file: {AUDIO_FILE}")
    audio_data = Path(AUDIO_FILE).read_bytes()
    fields = {
        "model": MODEL,
        "response_format": "verbose_json",
        "timestamp_granularities[]": "word",
        "language": LANGUAGE,
    }
    files = {"file": ("voiceover-audio.wav", audio_data, "audio/wav")}
    body, content_type = build_multipart(fields, files)
    print(f"Sending to Whisper API at {WHISPER_API_URL} ...")
    request = urllib.request.Request(
        WHISPER_API_URL, data=body, headers={"Content-Type": content_type},
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        data = json.loads(response.read().decode("utf-8"))
    captions = captions_from_response(data)
    write_captions(captions, OUTPUT_FILE)
    print(f"Saved {len(captions)} captions to {OUTPUT_FILE}")


def main():
    try:
        transcribe()
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        print(f"Whisper API error: {error.code} {detail}", file=sys.stderr)
        return 1
    except (OSError, ValueError) as error:
        print(f"Transcription failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
