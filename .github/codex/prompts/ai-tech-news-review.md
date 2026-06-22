Use `.claude/skills/ai-tech-news/SKILL.md` to audit the AI technology news automation in this pull request.

Run the unit tests and prompt dry-run. Review the workflow, citation rendering, source-quality rules,
timezone behavior, secret handling, report persistence, and failure modes. Fix only high-confidence issues
inside `src/ai_tech_news/`, `tests/ai_tech_news/`, `.claude/skills/ai-tech-news/`, `docs/ai-tech-news-automation.md`,
and `.github/workflows/ai-tech-news.yml`. Do not modify the stock-analysis product. Do not make a paid live API call
unless explicitly requested and `OPENAI_API_KEY` is already available. Finish with a concise verification summary and
remaining risks.
