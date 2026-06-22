"""Command-line entry point for the AI technology news automation."""

from __future__ import annotations

import argparse
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .prompts import build_prompt
from .report import ReportConfig, generate_report, persist_report


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a cited AI technology intelligence report")
    parser.add_argument("--mode", choices=["daily", "weekly"], default="daily")
    parser.add_argument("--lookback-hours", type=_positive_int)
    parser.add_argument("--model", default=os.getenv("AI_TECH_NEWS_MODEL") or "gpt-5.5")
    parser.add_argument(
        "--reasoning-effort",
        choices=["minimal", "low", "medium", "high", "xhigh"],
        default=os.getenv("AI_TECH_NEWS_REASONING_EFFORT") or "medium",
    )
    parser.add_argument("--language", default=os.getenv("AI_TECH_NEWS_LANGUAGE") or "zh-CN")
    parser.add_argument("--timezone", default=os.getenv("AI_TECH_NEWS_TIMEZONE") or "America/Los_Angeles")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(os.getenv("AI_TECH_NEWS_OUTPUT_DIR") or "reports/ai-tech-news"),
    )
    parser.add_argument(
        "--max-output-tokens",
        type=_positive_int,
        default=int(os.getenv("AI_TECH_NEWS_MAX_OUTPUT_TOKENS") or "16000"),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the research prompt without calling the API or writing files",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    lookback = args.lookback_hours or (168 if args.mode == "weekly" else 36)
    now = datetime.now(ZoneInfo(args.timezone))

    if args.dry_run:
        print(
            build_prompt(
                now=now,
                lookback_hours=lookback,
                mode=args.mode,
                language=args.language,
            )
        )
        return 0

    config = ReportConfig(
        mode=args.mode,
        lookback_hours=lookback,
        model=args.model,
        reasoning_effort=args.reasoning_effort,
        language=args.language,
        timezone_name=args.timezone,
        output_dir=args.output_dir,
        max_output_tokens=args.max_output_tokens,
    )
    report = generate_report(config, now=now)
    report_path, latest_path, metadata_path = persist_report(report, config)
    print(f"Report: {report_path}")
    print(f"Latest: {latest_path}")
    print(f"Metadata: {metadata_path}")
    print(f"Sources: {len(report.sources)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
