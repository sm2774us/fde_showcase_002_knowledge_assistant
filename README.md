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

---

## List of FDE Showcase Apps

| App Name | 🎯 Core Focus & Architecture | 🧬 Lineage & Progression | 💡 Key Use Cases | 💼 How to Showcase in Interviews |
| --- | --- | --- | --- | --- |
| **[1. FDE Discovery Analyzer](https://github.com/sm2774us/fde_showcase_001_discovery_analyzer/)** | ⚡ **Basic / Single-Turn**<br><br>• Structured outputs via provider JSON Schema<br><br>• Few-shot prompt engineering & data-delimited inputs<br><br>• Deterministic verifiers & Pydantic auto-repair loops ($\le 2$ retries)<br><br>• Single-pass CLI / Web UI / Golden Evals | 🎯 **Level 1: Entry Foundation**<br><br>Establishes reliable, single-turn LLM input/output contracts, schema enforcement, repair loops, and deterministic verification before attempting stateful or multi-step logic. | • Customer discovery call transformation (notes $\rightarrow$ validated Agentforce-style blueprints)<br><br>• Automated static analysis & Apex code review for bulk-safety<br><br>• Rapid MVP 5-day execution planning | **Highlight Systems Reliability & Schema Integrity:**<br><br>• Explain how you eliminate LLM output variance using forced schemas and auto-healing Pydantic loops.<br><br>• Emphasize your zero-SDK stdlib adapter approach to avoid vendor lock-in across Claude, OpenAI, Gemini, and Grok. |
| **[2. FDE Knowledge Assistant](https://github.com/sm2774us/fde_showcase_002_knowledge_assistant/)** | 🧠 **Intermediate / Grounded Context**<br><br>• Role-Based Access Control (RBAC/ACL) pre-filtering<br><br>• Hybrid search (BM25 + Dense Vectors combined via Reciprocal Rank Fusion)<br><br>• Heading/table-aware atomic chunking<br><br>• Input injection stripping & pre-prompt evidence gating<br><br>• Strict lexical citation verification | 📈 **Level 2: Contextual Escalation**<br><br>Evolves Level 1's single-turn validation into retrieval-augmented generation (RAG), focusing on enterprise data boundaries, security guardrails, context management, and hallucination prevention. | • Secure enterprise internal search & document Q&A<br><br>• Role-restricted knowledge access (e.g., HR vs. Employee compensation data)<br><br>• Injection-resistant document consumption<br><br>• Zero-hallucination support portals | **Highlight Enterprise Security & Groundedness:**<br><br>• Showcase the pre-retrieval ACL filtering that prevents restricted context from ever touching vector scoring or LLM prompts.<br><br>• Detail your anti-hallucination pipeline (evidence gate + lexical support check) that fails closed rather than guessing. |
| **[3. FDE Case Resolution Agent](https://github.com/sm2774us/fde_showcase_003_case_resolution_agent/)** | 🤖 **Advanced / Agentic Execution**<br><br>• Multi-step ReAct loop with loop detection & error streak fail-safes<br><br>• Model Context Protocol (MCP stdio JSON-RPC) tool execution<br><br>• Agent-to-Agent (A2A JSON-RPC) policy communication<br><br>• Deterministic Human-In-The-Loop (HITL) gates & OTel-shaped telemetry traces | 🚀 **Level 3: Operational Agentics**<br><br>Combines Level 1 output contracts and Level 2 security/RAG context into autonomous, multi-turn tool execution against production systems (SQLite/Salesforce CRM) with strict financial guardrails. | • Autonomous enterprise CRM case resolution (refunds, order updates, email drafting)<br><br>• Multi-agent policy enforcement & financial tier escalations<br><br>• Cross-tool integration via native MCP across IDEs (Claude Code, Copilot, Gemini CLI, Codex) | **Highlight Autonomous Control & Architecture:**<br><br>• Focus on safety controls: dual-key approval policies, hard-coded parameter stripping (`approved_by`), and loop/error fail-safes.<br><br>• Demo your cross-agent interop using MCP and A2A standard protocols with full audit tracing. |

---

### 🛣️ Narrative Lineage Across the 3 Apps

1. **[App 1 - Discovery Analyzer - (Validation Layer)](https://github.com/sm2774us/fde_showcase_001_discovery_analyzer/):** Proves you know how to talk to LLMs deterministically—getting structured data out without reliance on heavy frameworks, handling retries gracefully, and validating inputs/outputs against concrete business schemas.


2. **[App 2 - Knowledge Assistant - (Context & Security Layer)](https://github.com/sm2774us/fde_showcase_002_knowledge_assistant/):** Expands single-turn output validation into multi-source enterprise retrieval, proving you can handle data isolation, prompt injection attacks, hybrid search ranking, and zero-hallucination citation checks.


3. **[App 3 - Case Resolution Agent - (Action & Agentic Layer)](https://github.com/sm2774us/fde_showcase_003_case_resolution_agent/):** Translates validated structured outputs and secure context into autonomous system actions, orchestrating real tool calls via MCP, agent-to-agent negotiation, multi-turn error recovery, and strict human approval limits.

---

### 💡 Strategy: Demonstrating Technical Depth in Interviews

* **The FDE Engineering Philosophy:** Walk interviewers through how this trio covers the complete deployment spectrum—from **Discovery** (parsing customer intake accurately) to **Knowledge** (safely accessing enterprise context) to **Resolution** (executing workflows via tools with guardrails).

* **Offline-First Resilience:** Point out that all 3 apps run zero-dependency / offline test suites, mock layers, and golden evals without requiring API keys, proving your emphasis on testability and local CI/CD pipelines.

* **Standards over Lock-in:** Highlight your architectural choices—writing lightweight, vendor-agnostic adapters (`urllib`), implementing standard specs (MCP, A2A, JSON-Schema), and avoiding black-box agent frameworks in favor of explicit Python loop control.

---

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
