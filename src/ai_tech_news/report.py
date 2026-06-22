"""Generate, render, and persist a cited AI technology intelligence report."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

if TYPE_CHECKING:
    from openai import OpenAI

from .citations import Source, render_response_markdown
from .prompts import build_prompt


@dataclass(frozen=True)
class ReportConfig:
    """Runtime settings for one AI technology news report."""

    mode: str = "daily"
    lookback_hours: int = 36
    model: str = "gpt-5.5"
    reasoning_effort: str = "medium"
    language: str = "zh-CN"
    timezone_name: str = "America/Los_Angeles"
    output_dir: Path = Path("reports/ai-tech-news")
    max_output_tokens: int = 16000

    def validate(self) -> None:
        if self.mode not in {"daily", "weekly"}:
            raise ValueError("mode must be daily or weekly")
        if self.lookback_hours <= 0:
            raise ValueError("lookback_hours must be positive")
        if self.reasoning_effort not in {"minimal", "low", "medium", "high", "xhigh"}:
            raise ValueError("unsupported reasoning effort")
        if self.max_output_tokens < 2000:
            raise ValueError("max_output_tokens is too small for a useful report")
        _load_timezone(self.timezone_name)


@dataclass(frozen=True)
class GeneratedReport:
    """A rendered report plus metadata needed for persistence and audits."""

    markdown: str
    sources: list[Source]
    response_id: str | None
    usage: dict[str, Any] | None
    generated_at: datetime


def _load_timezone(timezone_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"unknown timezone: {timezone_name}") from exc


def _response_payload(response: Any) -> dict[str, Any]:
    if hasattr(response, "model_dump"):
        return response.model_dump(mode="json")
    if isinstance(response, dict):
        return response
    raise TypeError("Unsupported Responses API object")


def _normalized_now(now: datetime | None, timezone_name: str) -> datetime:
    timezone = _load_timezone(timezone_name)
    if now is None:
        return datetime.now(timezone)
    if now.tzinfo is None:
        return now.replace(tzinfo=timezone)
    return now.astimezone(timezone)


def generate_report(
    config: ReportConfig,
    *,
    client: "OpenAI" | Any | None = None,
    now: datetime | None = None,
) -> GeneratedReport:
    """Call the Responses API with web search and return rendered Markdown."""

    config.validate()
    generated_at = _normalized_now(now, config.timezone_name)

    prompt = build_prompt(
        now=generated_at,
        lookback_hours=config.lookback_hours,
        mode=config.mode,
        language=config.language,
    )

    api_key = os.getenv("OPENAI_API_KEY")
    if client is None and not api_key:
        raise RuntimeError("OPENAI_API_KEY is required for a live report")
    if client is None:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)

    response = client.responses.create(
        model=config.model,
        reasoning={"effort": config.reasoning_effort},
        tools=[{"type": "web_search"}],
        tool_choice="required",
        input=prompt,
        max_output_tokens=config.max_output_tokens,
        store=False,
    )
    payload = _response_payload(response)
    body, sources = render_response_markdown(payload)
    if not body:
        raise RuntimeError("The model returned no report text")
    if not sources:
        raise RuntimeError("The report contained no clickable web citations")

    metadata_header = (
        "---\n"
        f"generated_at: {generated_at.isoformat()}\n"
        f"timezone: {config.timezone_name}\n"
        f"mode: {config.mode}\n"
        f"lookback_hours: {config.lookback_hours}\n"
        f"model: {config.model}\n"
        f"reasoning_effort: {config.reasoning_effort}\n"
        f"source_count: {len(sources)}\n"
        "---\n\n"
    )
    return GeneratedReport(
        markdown=metadata_header + body.rstrip() + "\n",
        sources=sources,
        response_id=payload.get("id"),
        usage=payload.get("usage"),
        generated_at=generated_at,
    )


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(content)
        temp_path = Path(handle.name)
    temp_path.replace(path)


def persist_report(report: GeneratedReport, config: ReportConfig) -> tuple[Path, Path, Path]:
    """Write dated report, latest symlink-equivalent copy, and JSON metadata."""

    timezone = _load_timezone(config.timezone_name)
    local_date = report.generated_at.astimezone(timezone).date()
    dated_dir = config.output_dir / f"{local_date:%Y}" / f"{local_date:%m}"
    suffix = "weekly" if config.mode == "weekly" else "daily"
    report_path = dated_dir / f"{local_date.isoformat()}-{suffix}.md"
    latest_path = config.output_dir / "latest.md"
    metadata_path = dated_dir / f"{local_date.isoformat()}-{suffix}.json"

    _atomic_write(report_path, report.markdown)
    latest_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=latest_path.parent, delete=False) as handle:
        temp_latest = Path(handle.name)
    shutil.copyfile(report_path, temp_latest)
    temp_latest.replace(latest_path)

    metadata = {
        "generated_at": report.generated_at.isoformat(),
        "timezone": config.timezone_name,
        "mode": config.mode,
        "lookback_hours": config.lookback_hours,
        "model": config.model,
        "reasoning_effort": config.reasoning_effort,
        "response_id": report.response_id,
        "usage": report.usage,
        "sources": [asdict(source) for source in report.sources],
        "report_path": str(report_path),
    }
    _atomic_write(metadata_path, json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
    return report_path, latest_path, metadata_path
