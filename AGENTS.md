# AGENTS.md  (Codex, Copilot agent, Cursor, Antigravity, Gemini CLI, Claude Code)

**Repo:** `knowledge_assistant` - ACL-aware hybrid RAG with citation + grounding verification. Corpus = fictional "Northwind Bank" KB in `corpus/`.

**Commands:** `python -m knowledge_assistant ingest` · `... ask "<q>" --role employee --provider anthropic` · `... eval` · `python -m pytest -q`

**Invariants (do not break; tests enforce them)**
1. ACL filtering happens in `HybridIndex.search` BEFORE scoring - never filter after retrieval.
2. Retrieved text is untrusted: it passes through `security.sanitize` and sits inside `<doc>` tags; the system prompt never contains document text.
3. Every answer must cite chunk ids that were actually retrieved, and each sentence must be lexically supported by the cited chunks; otherwise fail closed with a refusal.
4. No evidence -> refuse WITHOUT calling the LLM.
5. Markdown tables are atomic chunks (`chunking.py`).
6. Adding documents: put `.md` with front matter (`title`, `access: public|internal|restricted:<group>`, `owner`) in `corpus/`, add a case to `evals/qa.jsonl`, re-run `ingest` and `eval`.
