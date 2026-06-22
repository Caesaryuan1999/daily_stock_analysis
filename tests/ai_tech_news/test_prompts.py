from __future__ import annotations

import unittest
from datetime import datetime, timezone

from ai_tech_news.prompts import build_prompt


class PromptTests(unittest.TestCase):
    def test_daily_prompt_contains_window_and_quality_controls(self) -> None:
        prompt = build_prompt(
            now=datetime(2026, 6, 22, 15, 0, tzinfo=timezone.utc),
            lookback_hours=36,
            mode="daily",
            language="zh-CN",
        )

        self.assertIn("past 36 hours", prompt)
        self.assertIn("AI 技术情报日报", prompt)
        self.assertIn("Cite every material factual claim inline", prompt)
        self.assertIn("China", prompt)
        self.assertIn("可能被高估", prompt)

    def test_rejects_invalid_mode(self) -> None:
        with self.assertRaises(ValueError):
            build_prompt(
                now=datetime.now(timezone.utc),
                lookback_hours=24,
                mode="monthly",
                language="zh-CN",
            )


if __name__ == "__main__":
    unittest.main()
