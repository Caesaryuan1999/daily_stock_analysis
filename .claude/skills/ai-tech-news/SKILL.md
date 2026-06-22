---
name: ai-tech-news
description: Run, verify, troubleshoot, or improve the repository's cited AI technology news automation and trend-analysis reports.
---

# AI Technology News Automation

`AGENTS.md` is the repository rule source. Use this skill when asked to generate an AI technology briefing, inspect the scheduled workflow, fix report failures, improve source quality, or evaluate the technology-radar methodology.

## Workflow

1. Read `AGENTS.md`, `docs/ai-tech-news-automation.md`, `.github/workflows/ai-tech-news.yml`, and the relevant `src/ai_tech_news/` files.
2. Keep changes isolated from the stock-analysis product unless integration is explicitly requested.
3. Run:

   ```bash
   PYTHONPATH=src python -m unittest discover -s tests/ai_tech_news -v
   PYTHONPATH=src python -m ai_tech_news --mode daily --dry-run
   ```

4. For a live report, require `OPENAI_API_KEY`; never print or persist the key.
5. Validate that the report:
   - used web search and contains clickable inline citations;
   - prioritizes primary sources and exact publication dates;
   - separates announcements, demos, preprints, independent validation, and production deployments;
   - covers the ten technical, business, safety, governance, and geography dimensions in the prompt;
   - distinguishes real capability changes from packaging, scaling, pricing, benchmark tuning, and marketing;
   - states uncertainty and does not invent facts or sources.
6. Make minimal, reviewable changes. Preserve generated-report history and `latest.md` behavior.

## Definition of done

- Unit tests and dry-run pass.
- Workflow YAML remains scheduled for 08:05 America/Los_Angeles.
- No secret is committed.
- Any live report has source metadata and at least one clickable cited source.
- Summarize commands run, files changed, residual risks, and any API-dependent verification not performed.
