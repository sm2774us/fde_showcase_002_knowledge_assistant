"""Offline extractive 'LLM': picks the best-overlapping sentences from the <doc> blocks and cites them."""
from __future__ import annotations

import json
import re

from .llm import LLM, LLMResponse
from .text import tokens


class MockLLM(LLM):
    provider = "mock"

    def __init__(self, model=None):
        super().__init__(model or "mock-extractive-1")

    def chat(self, system, messages, *, tools=None, json_schema=None, schema_name="output"):
        user = messages[-1]["content"]
        q = set(tokens(re.search(r"Question: (.*)", user).group(1)))
        cands, bodies = [], {}
        for m in re.finditer(r'<doc id="([^"]+)"[^>]*section="([^"]*)">\n(.*?)\n</doc>', user, re.S):
            cid, head, body = m.groups()
            hq = len(q & set(tokens(head)))
            is_tbl = '|' in body
            bodies[cid] = body
            for line in body.splitlines():
                line = line.strip()
                if not line or set(line) <= set("|-: "):
                    continue
                for s in re.split(r"(?<=[.!?])\s+", line):
                    score = len(q & set(tokens(s))) + (hq if is_tbl and len(q & set(tokens(s))) else 0)
                    if score:
                        cands.append((score, cid, s.strip(" |")))
        cands.sort(key=lambda x: -x[0])
        top = cands[0][0] if cands else 0
        picked = [c for c in cands if c[0] >= max(1, 0.6 * top)][:4]
        if picked and '|' in bodies[picked[0][1]]:   # best hit lives in a table: return the whole table, row by row
            rows = [", ".join(c.strip() for c in l.strip("| ").split("|")) for l in bodies[picked[0][1]].splitlines() if l.strip().startswith("|") and not set(l) <= set("|-: ")]
            picked = picked[:1] + [(0, picked[0][1], "Table: " + "; ".join(rows))]
        if not picked:
            out = {"answer": "", "citations": [], "insufficient_evidence": True}
        else:
            out = {"answer": " ".join(s if s.endswith((".", "!", "?")) else s + "." for _, _, s in picked),
                   "citations": sorted({c for _, c, _ in picked}), "insufficient_evidence": False}
        return LLMResponse(json.dumps(out), [], {"input_tokens": len(user) // 4, "output_tokens": 80}, self.provider, self.model)
