"""Hybrid index: BM25 (sparse) + dense vectors, fused with Reciprocal Rank Fusion, behind an ACL pre-filter."""
from __future__ import annotations

import json
import math
import pathlib
from collections import Counter
from dataclasses import dataclass

from .chunking import Chunk, chunk_corpus
from .embeddings import get_embedder
from .security import allowed
from .text import tokens


@dataclass
class Hit:
    chunk: Chunk
    rrf: float
    bm25: float
    dense: float


class HybridIndex:
    def __init__(self, chunks: list[Chunk], vectors: list[list[float]], embedder):
        self.chunks, self.vectors, self.embedder = chunks, vectors, embedder
        self.toks = [tokens(c.title + " " + c.heading + " " + c.text) for c in chunks]
        self.df = Counter(t for ts in self.toks for t in set(ts))
        self.avg = sum(len(t) for t in self.toks) / max(1, len(self.toks))

    @classmethod
    def build(cls, corpus_dir, embedder_name=None):
        chunks = chunk_corpus(corpus_dir)
        emb = get_embedder(embedder_name)
        return cls(chunks, emb.embed([f"{c.title}. {c.heading}. {c.text}" for c in chunks]), emb)

    def save(self, path):
        p = pathlib.Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"embedder": self.embedder.name, "chunks": [c.to_dict() for c in self.chunks], "vectors": self.vectors}))

    @classmethod
    def load(cls, path, embedder_name=None):
        d = json.loads(pathlib.Path(path).read_text())
        emb = get_embedder(embedder_name or ("hash" if d["embedder"].startswith("hash") else d["embedder"].split(":")[0]))
        if emb.name != d["embedder"]:
            raise ValueError(f"index built with {d['embedder']} but query embedder is {emb.name}; re-run ingest")
        return cls([Chunk(**c) for c in d["chunks"]], d["vectors"], emb)

    def _bm25(self, q: list[str], i: int, k1=1.5, b=0.75) -> float:
        tf, n = Counter(self.toks[i]), len(self.chunks)
        s = 0.0
        for t in set(q):
            if t in tf:
                idf = math.log(1 + (n - self.df[t] + 0.5) / (self.df[t] + 0.5))
                s += idf * tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * len(self.toks[i]) / self.avg))
        return s

    def search(self, query: str, role: str, k: int = 5, mode: str = "hybrid") -> list[Hit]:
        # 1) ACL PRE-FILTER: restricted chunks never enter scoring, ranking or the prompt.
        ids = [i for i, c in enumerate(self.chunks) if allowed(role, c.access)]
        q = tokens(query)
        qv = self.embedder.embed([query])[0]
        bm = {i: self._bm25(q, i) for i in ids}
        dn = {i: sum(a * b for a, b in zip(qv, self.vectors[i])) for i in ids}
        rank = lambda sc: {i: r for r, i in enumerate(sorted((i for i in ids if sc[i] > 0), key=lambda i: -sc[i]), 1)}
        rb, rd = rank(bm), rank(dn)
        out = []
        for i in ids:
            r = 0.0
            if mode in ("hybrid", "bm25") and i in rb:
                r += 1 / (60 + rb[i])
            if mode in ("hybrid", "dense") and i in rd:
                r += 1 / (60 + rd[i])
            if r > 0:
                out.append(Hit(self.chunks[i], r, bm[i], dn[i]))
        return sorted(out, key=lambda h: -h.rrf)[:k]
