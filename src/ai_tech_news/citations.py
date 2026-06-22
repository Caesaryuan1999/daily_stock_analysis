"""Utilities for turning Responses API citation annotations into Markdown links."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable
from urllib.parse import urlparse


@dataclass(frozen=True)
class Source:
    """A unique cited source extracted from a model response."""

    number: int
    title: str
    url: str


def _valid_http_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _escape_markdown_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def _iter_output_text(payload: dict[str, Any]) -> Iterable[dict[str, Any]]:
    for item in payload.get("output", []):
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if isinstance(content, dict) and content.get("type") == "output_text":
                yield content


def render_response_markdown(payload: dict[str, Any]) -> tuple[str, list[Source]]:
    """Render model text with clickable inline citations and a deduplicated source list.

    Responses API citations are represented as annotations with character offsets. The
    annotated marker is replaced with a normal Markdown link. Invalid annotations are
    ignored rather than allowing malformed data to corrupt the report.
    """

    url_to_source: dict[str, Source] = {}
    rendered_parts: list[str] = []

    def register_source(title: Any, url: str) -> Source:
        existing = url_to_source.get(url)
        if existing is not None:
            return existing
        clean_title = str(title or url).strip() or url
        source = Source(number=len(url_to_source) + 1, title=clean_title, url=url)
        url_to_source[url] = source
        return source

    for content in _iter_output_text(payload):
        text = str(content.get("text") or "")
        annotations = content.get("annotations") or []
        grouped: dict[tuple[int, int], list[Source]] = {}
        trailing: list[Source] = []

        sortable_annotations = []
        for annotation in annotations:
            if not isinstance(annotation, dict) or annotation.get("type") != "url_citation":
                continue
            url = annotation.get("url")
            if not _valid_http_url(url):
                continue
            start = annotation.get("start_index")
            sort_start = start if isinstance(start, int) else len(text)
            sortable_annotations.append((sort_start, annotation))

        for _, annotation in sorted(sortable_annotations, key=lambda item: item[0]):
            source = register_source(annotation.get("title"), annotation["url"])
            start = annotation.get("start_index")
            end = annotation.get("end_index")
            if isinstance(start, int) and isinstance(end, int) and 0 <= start <= end <= len(text):
                grouped.setdefault((start, end), []).append(source)
            else:
                trailing.append(source)

        for (start, end), sources in sorted(grouped.items(), reverse=True):
            marker = "".join(f"[[{source.number}]]({source.url})" for source in sources)
            text = text[:start] + marker + text[end:]

        if trailing:
            text = text.rstrip() + " " + "".join(f"[[{source.number}]]({source.url})" for source in trailing)

        if text.strip():
            rendered_parts.append(text.strip())

    sources = list(url_to_source.values())
    body = "\n\n".join(rendered_parts).strip()
    if sources:
        source_lines = ["## 自动提取的参考来源"]
        for source in sources:
            title = _escape_markdown_label(source.title)
            source_lines.append(f"{source.number}. [{title}]({source.url})")
        body = f"{body}\n\n" + "\n".join(source_lines)

    return body, sources
