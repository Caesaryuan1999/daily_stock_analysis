# AI 技术新闻自动化

本自动化用于生成带可点击引用的 AI 技术情报日报或周报。它与股票分析主流程解耦，代码位于 `src/ai_tech_news/`，输出位于 `reports/ai-tech-news/`。

## 覆盖维度

报告默认覆盖十个维度：基础模型与推理、多模态、Agent 与编码/电脑操作、机器人、芯片与推理效率、数据/RAG/记忆、研究与开源、安全与评测、商业化，以及全球治理与区域生态。重大动态会标注成熟度、证据强度和主要风险，并区分公告、演示、预印本、开源发布、有限预览、早期生产和规模化生产。

## GitHub Actions 调度

工作流文件：`.github/workflows/ai-tech-news.yml`。

- 默认每天 `08:05 America/Los_Angeles` 运行。工作流使用两个 UTC cron 触发器加本地时间门控，以兼容夏令时。
- 日报默认回溯 36 小时；周报默认回溯 168 小时。
- 手动运行入口：`Actions -> AI 技术情报日报 -> Run workflow`。
- 生成文件：`reports/ai-tech-news/YYYY/MM/YYYY-MM-DD-daily.md` 或 `weekly.md`，并同步更新 `reports/ai-tech-news/latest.md`。

## 配置

在 `Settings -> Secrets and variables -> Actions` 中配置：

| 类型 | 名称 | 必填 | 说明 |
| --- | --- | --- | --- |
| Secret | `OPENAI_API_KEY` | 是 | OpenAI 官方 API Key；需要支持 Responses API 和 hosted web search。 |
| Variable | `AI_TECH_NEWS_MODEL` | 否 | 默认 `gpt-5.5`。 |
| Variable | `AI_TECH_NEWS_REASONING_EFFORT` | 否 | 默认 `medium`，可选 `minimal/low/medium/high/xhigh`。 |
| Variable | `AI_TECH_NEWS_LANGUAGE` | 否 | 默认 `zh-CN`。 |

不要在仓库、报告或日志中写入 API Key。第三方 OpenAI-compatible 代理未必支持 hosted web search，因此该自动化默认使用 OpenAI 官方 Responses API。

## 本地验证

```bash
PYTHONPATH=src python -m unittest discover -s tests/ai_tech_news -v
PYTHONPATH=src python -m ai_tech_news --mode daily --dry-run
```

生成真实报告需要 `OPENAI_API_KEY`：

```bash
export OPENAI_API_KEY="..."
PYTHONPATH=src python -m ai_tech_news --mode daily
PYTHONPATH=src python -m ai_tech_news --mode weekly
PYTHONPATH=src python -m ai_tech_news --mode daily --lookback-hours 72
```

可选环境变量：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `AI_TECH_NEWS_MODEL` | `gpt-5.5` | 报告模型。 |
| `AI_TECH_NEWS_REASONING_EFFORT` | `medium` | 推理强度。 |
| `AI_TECH_NEWS_LANGUAGE` | `zh-CN` | 报告语言。 |
| `AI_TECH_NEWS_TIMEZONE` | `America/Los_Angeles` | 报告日期与调度时区。 |
| `AI_TECH_NEWS_OUTPUT_DIR` | `reports/ai-tech-news` | 输出目录。 |
| `AI_TECH_NEWS_MAX_OUTPUT_TOKENS` | `16000` | 最大输出 token。 |

## Codex 质检与执行

仓库 skill 位于 `.claude/skills/ai-tech-news/SKILL.md`，PR 审查提示词位于 `.github/codex/prompts/ai-tech-news-review.md`。让 Codex 处理该自动化时，应要求它先运行单元测试与 dry-run，再检查引用渲染、时区门控、secret 处理、报告落盘和工作流权限。除非明确需要并且环境中已存在 `OPENAI_API_KEY`，不要让 Codex 发起真实付费报告调用。

## 可靠性与限制

- 请求强制使用 hosted web search，并要求报告包含可点击引用。
- API 返回的引用注解会转换为 Markdown 链接，同时写入去重后的来源列表和 JSON 元数据。
- 提示词优先使用论文、系统卡、官方发布、代码仓库、标准和监管文件，并要求对厂商基准保持审慎。
- 自动化能提高覆盖面，但不能替代对高影响结论的人工复核，尤其是未独立复现的基准、预印本和厂商声明。
- 每次运行会产生模型推理和联网搜索费用；可通过更低推理强度、更短窗口或更经济的可用模型控制成本。
