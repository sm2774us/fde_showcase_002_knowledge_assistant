# FDE Knowledge Assistant

> **Showcase app 2 of 3** - *Intermediate / grounded context: RAG, embeddings, context management, hallucination guardrails.*
> The assistant an FDE leaves behind in a customer's environment: it answers from **the customer's own documents**, **respects who is asking**, **cites its sources**, and **refuses** when it can't prove an answer.

```
question + role ─► input guardrail (injection patterns)
        │
        ▼
 ACL PRE-FILTER (role → allowed access labels)  ◄── restricted chunks never enter scoring or the prompt
        ▼
 BM25 (sparse)  +  dense vectors  ──►  Reciprocal Rank Fusion  ──► top-k
        ▼
 sanitize retrieved text (strip instruction-like sentences) ─► <doc id=...> data blocks
        ▼
 evidence gate (query-term coverage) ── no evidence ──► refuse, NO LLM call
        ▼
 LLM (Claude / OpenAI / Gemini / Grok) → JSON {answer, citations[], insufficient_evidence}
        ▼
 verify: cited ids ⊆ retrieved ids · every sentence lexically supported by cited chunks · else fail closed
        ▼
 answer + sources + audit log (hashed question, chunk ids, outcome)
```

## Quick start (offline, zero dependencies)
```bash
python -m knowledge_assistant ingest
python -m knowledge_assistant ask "What is the retry policy for failed webhooks?"
python -m knowledge_assistant ask "What are the executive compensation bands?"              # refused (employee)
python -m knowledge_assistant ask "What are the executive compensation bands?" --role hr    # answered
python -m knowledge_assistant ask "What does a new vendor need to complete during onboarding?"  # poisoned doc: injection stripped
python -m knowledge_assistant eval        # 14 cases + ablation: ACL leaks=0, injection leaks=0
python -m knowledge_assistant serve       # http://localhost:8081
python -m pytest -q
```
Live models: set a key (`.env.example`) and add `--provider anthropic|openai|gemini|xai|auto`. Real embeddings: `python -m knowledge_assistant ingest --embedder openai|gemini` (Claude has no embeddings API - pair it with OpenAI/Gemini/Voyage embeddings). The default `hash` embedder is an offline feature-hashing stand-in so everything is testable without keys.

## Key techniques
| Concern | Implementation |
|---|---|
| Chunking | Heading-aware; **tables are atomic** (retry-policy table never severed) - `chunking.py` |
| Retrieval | BM25 + dense + RRF; `--mode bm25\|dense\|hybrid`; `eval` prints an ablation |
| Access control | Pre-filter on `access:` front-matter label by role (`security.ROLES`) |
| Prompt injection | Input patterns, line-level sanitizer for retrieved text, docs wrapped as data, system prompt never contains doc text |
| Hallucination | Evidence gate, JSON-schema output, citation validity, per-sentence support check, fail closed |
| Audit | `.index/audit.jsonl` - role, hashed question, chunk ids, outcome (no raw text) |

## AI-tooling integration
`AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, and the skill in `.claude/skills/` + `.agent/skills/` (Claude Code, Antigravity, Gemini CLI).

## Honest limits
On this tiny 25-chunk corpus all three retrieval modes saturate at 10/10, so the bundled ablation proves the harness works, not that hybrid wins - run `eval` on your customer's corpus for the real comparison. Sentence-support check is lexical (cheap, deterministic) - for paraphrase-heavy answers add an NLI/LLM verifier. The bundled corpus is fictional. Sanitizer is pattern-based: it is one layer, not a guarantee; real deployments also need output filtering and least-privilege tools.
