from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from ai_tech_news.report import ReportConfig, generate_report, persist_report


class FakeResponse:
    def model_dump(self, mode: str = "json") -> dict:
        del mode
        text = "# AI 技术情报日报\n\nVerified claim CITATION."
        return {
            "id": "resp_test",
            "status": "completed",
            "usage": {"input_tokens": 10, "output_tokens": 20},
            "output": [
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": text,
                            "annotations": [
                                {
                                    "type": "url_citation",
                                    "start_index": text.index("CITATION"),
                                    "end_index": text.index("CITATION") + len("CITATION"),
                                    "url": "https://example.com/source",
                                    "title": "Source",
                                }
                            ],
                        }
                    ],
                }
            ],
        }


class FakeResponses:
    def __init__(self) -> None:
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return FakeResponse()


class FakeClient:
    def __init__(self) -> None:
        self.responses = FakeResponses()


class ReportTests(unittest.TestCase):
    def test_generate_and_persist_report(self) -> None:
        fake_client = FakeClient()
        with tempfile.TemporaryDirectory() as directory:
            config = ReportConfig(output_dir=Path(directory), max_output_tokens=4000)
            # 02:00 UTC on June 23 is still June 22 in America/Los_Angeles.
            now = datetime(2026, 6, 23, 2, 0, tzinfo=timezone.utc)
            report = generate_report(config, client=fake_client, now=now)
            report_path, latest_path, metadata_path = persist_report(report, config)

            self.assertEqual(Path(directory) / "2026" / "06" / "2026-06-22-daily.md", report_path)
            self.assertTrue(report_path.exists())
            self.assertTrue(latest_path.exists())
            self.assertTrue(metadata_path.exists())
            latest = latest_path.read_text(encoding="utf-8")
            self.assertIn("source_count: 1", latest)
            self.assertIn("timezone: America/Los_Angeles", latest)
            self.assertEqual("required", fake_client.responses.kwargs["tool_choice"])
            self.assertEqual([{"type": "web_search"}], fake_client.responses.kwargs["tools"])
            self.assertFalse(fake_client.responses.kwargs["store"])

    def test_live_generation_requires_api_key(self) -> None:
        config = ReportConfig(max_output_tokens=4000)
        with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
            with self.assertRaises(RuntimeError):
                generate_report(config, client=None)

    def test_rejects_unknown_timezone(self) -> None:
        config = ReportConfig(timezone_name="Mars/Olympus")
        with self.assertRaises(ValueError):
            config.validate()


if __name__ == "__main__":
    unittest.main()
