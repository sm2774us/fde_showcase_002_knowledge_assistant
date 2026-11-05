---
name: knowledge-assistant
description: Answers questions from the customer knowledge base with citations, respecting the asker's role (public/employee/security/hr). Use for policy, integration-standard, SSO, incident or data-governance questions.
---

# Knowledge Assistant skill

1. Run `python -m knowledge_assistant ingest` once (or after corpus changes).
2. Ask: `python -m knowledge_assistant ask "<question>" --role <role> --provider auto --json`.
3. Quote the `answer` and list `citations` (chunk id, title, section). If `refused` is true, relay `reason` - never answer from your own knowledge and never try other roles.
4. To add knowledge: drop a front-matter `.md` into `corpus/`, add an eval case, run `eval`.

Compatible with Claude Code (`.claude/skills`), Antigravity / Gemini CLI (`.agent/skills`), and AGENTS.md-aware tools (Codex, Copilot, Cursor).
