"""Offline tests only: synthetic audio/JSON and mocked HTTP responses."""
from contextlib import chdir, redirect_stderr, redirect_stdout
from email.parser import BytesParser
from email.policy import default
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "transcribe", ROOT / "skills/tutorial-video-creator/scripts/transcribe-template.py"
)
transcribe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(transcribe)
FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class CaptionTests(unittest.TestCase):
    def test_top_level_words_and_unicode(self):
        captions = transcribe.captions_from_response(fixture("words.json"))
        self.assertEqual("".join(c["text"] for c in captions), "Привет, мир!")
        self.assertEqual(captions[0], {
            "text": "Привет,", "startMs": 125, "endMs": 500,
            "timestampMs": 125, "confidence": None,
        })
        self.assertEqual(captions[1]["endMs"], 1250)

    def test_mixed_segment_words_do_not_drop_fallback_segments(self):
        captions = transcribe.captions_from_response(fixture("mixed-segments.json"))
        self.assertEqual([c["text"] for c in captions],
                         ["Первое", " слово", " второй", " сегмент"])
        self.assertEqual([c["startMs"] for c in captions], [0, 400, 1000, 2000])
        self.assertEqual(captions[-1]["endMs"], 3000)

    def test_top_level_words_take_precedence(self):
        data = fixture("words.json")
        data["segments"] = fixture("mixed-segments.json")["segments"]
        self.assertEqual(len(transcribe.captions_from_response(data)), 2)

    def test_segment_only_fallback_handles_empty_words(self):
        data = {"words": [], "segments": [
            {"start": 2, "end": 3, "text": " one  two ", "words": []}
        ]}
        captions = transcribe.captions_from_response(data)
        self.assertEqual([c["text"] for c in captions], ["one", " two"])
        self.assertEqual([c["startMs"] for c in captions], [2000, 2500])

    def test_invalid_responses(self):
        for data in (None, [], {}, {"text": "no timing"}, {"words": "bad"},
                     {"words": [None]}, {"segments": "bad"}, {"segments": [None]},
                     {"segments": [{"text": 1}]},
                     {"segments": [{"text": "   ", "start": 0, "end": 1}]}):
            with self.subTest(data=data), self.assertRaises(ValueError):
                transcribe.captions_from_response(data)

    def test_invalid_word_times_and_text(self):
        invalid = [
            {"word": "a", "start": 2, "end": 1},
            {"word": "a", "start": -1, "end": 1},
            {"word": "a", "start": "0", "end": 1},
            {"word": "a", "start": True, "end": 1},
            {"word": "a", "start": float("nan"), "end": 1},
            {"word": "a", "start": 0, "end": float("inf")},
            {"word": "a", "start": 0},
            {"word": None, "start": 0, "end": 1},
        ]
        for word in invalid:
            with self.subTest(word=word), self.assertRaises(ValueError):
                transcribe.captions_from_response({"words": [word]})

    def test_invalid_segment_times(self):
        with self.assertRaises(ValueError):
            transcribe.captions_from_response({"segments": [
                {"text": "one two", "start": 2, "end": 1}
            ]})


class MultipartTests(unittest.TestCase):
    def test_multipart_preserves_binary_data_and_fields(self):
        audio = b"RIFF\x00\xff\r\n----PythonFormBoundary7MA4YWxkTrZu0gW\r\n"
        body, content_type = transcribe.build_multipart(
            {"model": "test", "language": "ru", "timestamp_granularities[]": "word"},
            {"file": ("voiceover-audio.wav", audio, "audio/wav")},
        )
        message = BytesParser(policy=default).parsebytes(
            f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode() + body
        )
        parts = list(message.iter_parts())
        self.assertEqual(len(parts), 4)
        self.assertEqual(parts[2].get_param("name", header="content-disposition"),
                         "timestamp_granularities[]")
        self.assertEqual(parts[2].get_payload(decode=True), b"word")
        self.assertEqual(parts[-1].get_filename(), "voiceover-audio.wav")
        self.assertEqual(parts[-1].get_content_type(), "audio/wav")
        self.assertEqual(parts[-1].get_payload(decode=True), audio)
        self.assertNotEqual(content_type, transcribe.build_multipart({}, {})[1])


class TranscriptionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.audio = self.root / "audio.wav"
        self.audio.write_bytes(b"synthetic audio fixture")
        self.output = self.root / "public/captions.json"
        for name, value in (("AUDIO_FILE", self.audio), ("OUTPUT_FILE", self.output)):
            patcher = patch.object(transcribe, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.stdout, self.stderr = io.StringIO(), io.StringIO()

    def run_main(self):
        with redirect_stdout(self.stdout), redirect_stderr(self.stderr):
            return transcribe.main()

    def test_successful_request_writes_utf8_and_uses_timeout(self):
        response = io.BytesIO(json.dumps(fixture("words.json")).encode())
        with patch.object(transcribe.urllib.request, "urlopen", return_value=response) as request:
            self.assertEqual(self.run_main(), 0)
        self.assertIn("Привет", self.output.read_text(encoding="utf-8"))
        self.assertEqual(request.call_args.kwargs["timeout"], 300)
        self.assertEqual(request.call_args.args[0].get_method(), "POST")
        self.assertEqual(list(self.output.parent.glob("*.tmp")), [])

    def test_missing_audio_never_requests_api(self):
        self.audio.unlink()
        with patch.object(transcribe.urllib.request, "urlopen") as request:
            self.assertEqual(self.run_main(), 1)
            request.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_bad_responses_preserve_existing_captions(self):
        self.output.parent.mkdir()
        self.output.write_text("existing captions")
        for raw in (b"not JSON", b"[]", b'{"text":"missing timing"}', b"\xff"):
            with self.subTest(raw=raw), patch.object(
                transcribe.urllib.request, "urlopen", return_value=io.BytesIO(raw)
            ):
                self.assertEqual(self.run_main(), 1)
                self.assertEqual(self.output.read_text(), "existing captions")

    def test_network_errors_are_reported_without_tracebacks(self):
        errors = [urllib.error.URLError("unavailable"), TimeoutError("timed out"),
                  urllib.error.HTTPError("http://localhost", 500, "error", {}, io.BytesIO(b"\xff"))]
        for error in errors:
            with self.subTest(error=error), patch.object(
                transcribe.urllib.request, "urlopen", side_effect=error
            ):
                self.assertEqual(self.run_main(), 1)
                self.assertFalse(self.output.exists())
        self.assertNotIn("Traceback", self.stderr.getvalue())

    def test_atomic_replace_failure_preserves_output_and_cleans_temporary(self):
        self.output.parent.mkdir()
        self.output.write_text("existing captions")
        with patch.object(transcribe.os, "replace", side_effect=OSError("disk error")):
            with self.assertRaises(OSError):
                transcribe.write_captions([], self.output)
        self.assertEqual(self.output.read_text(), "existing captions")
        self.assertEqual(list(self.output.parent.iterdir()), [self.output])

    def test_output_in_current_directory(self):
        # No parent component should not cause os.makedirs('') to fail.
        with chdir(self.root):
            transcribe.write_captions([], "captions.json")
        self.assertEqual(json.loads((self.root / "captions.json").read_text()), [])


if __name__ == "__main__":
    unittest.main()
