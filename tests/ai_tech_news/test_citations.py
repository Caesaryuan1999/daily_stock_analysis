from __future__ import annotations

import unittest

from ai_tech_news.citations import render_response_markdown


class CitationRenderingTests(unittest.TestCase):
    def test_replaces_annotation_with_clickable_markdown_and_source_list(self) -> None:
        payload = {
            "output": [
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": "A claim CITATION.",
                            "annotations": [
                                {
                                    "type": "url_citation",
                                    "start_index": 8,
                                    "end_index": 16,
                                    "url": "https://example.com/research",
                                    "title": "Primary research",
                                }
                            ],
                        }
                    ],
                }
            ]
        }

        markdown, sources = render_response_markdown(payload)

        self.assertIn("A claim [[1]](https://example.com/research).", markdown)
        self.assertIn("1. [Primary research](https://example.com/research)", markdown)
        self.assertEqual(1, len(sources))

    def test_deduplicates_repeated_urls(self) -> None:
        payload = {
            "output": [
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": "X A and B.",
                            "annotations": [
                                {
                                    "type": "url_citation",
                                    "start_index": 2,
                                    "end_index": 3,
                                    "url": "https://example.com/a",
                                    "title": "A",
                                },
                                {
                                    "type": "url_citation",
                                    "start_index": 8,
                                    "end_index": 9,
                                    "url": "https://example.com/a",
                                    "title": "A duplicate",
                                },
                            ],
                        }
                    ],
                }
            ]
        }

        markdown, sources = render_response_markdown(payload)

        self.assertEqual(1, len(sources))
        self.assertEqual(2, markdown.count("[[1]](https://example.com/a)"))
        self.assertEqual(1, markdown.count("1. [A](https://example.com/a)"))

    def test_ignores_non_http_citations(self) -> None:
        payload = {
            "output": [
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": "Unsafe marker.",
                            "annotations": [
                                {
                                    "type": "url_citation",
                                    "start_index": 7,
                                    "end_index": 13,
                                    "url": "javascript:alert(1)",
                                    "title": "Unsafe",
                                }
                            ],
                        }
                    ],
                }
            ]
        }

        markdown, sources = render_response_markdown(payload)

        self.assertEqual("Unsafe marker.", markdown)
        self.assertEqual([], sources)


if __name__ == "__main__":
    unittest.main()
