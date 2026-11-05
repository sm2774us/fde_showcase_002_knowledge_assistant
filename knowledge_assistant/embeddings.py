"""Embedders. `hash` is offline & deterministic (signed feature hashing of unigrams/bigrams); `openai`/`gemini` call REST APIs."""
from __future__ import annotations

import hashlib
import json
import math
import os
import urllib.request

from .text import tokens


def _norm(v):
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


class HashEmbedder:
    name, dim = "hash-512", 512

    def embed(self, texts: list[str]) -> list[list[float]]:
        out = []
        for t in texts:
            v = [0.0] * self.dim
            toks = tokens(t)
            feats = toks + [a + "_" + b for a, b in zip(toks, toks[1:])]
            for f in feats:
                h = int.from_bytes(hashlib.blake2b(f.encode(), digest_size=8).digest(), "big")
                v[h % self.dim] += 1.0 if (h >> 63) & 1 else -1.0
            out.append(_norm(v))
        return out


def _post(url, headers, payload):
    req = urllib.request.Request(url, json.dumps(payload).encode(), {"content-type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


class OpenAIEmbedder:
    def __init__(self, model="text-embedding-3-small"):
        self.model, self.name = model, f"openai:{model}"

    def embed(self, texts):
        d = _post("https://api.openai.com/v1/embeddings", {"authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"}, {"model": self.model, "input": texts})
        return [_norm(x["embedding"]) for x in d["data"]]


class GeminiEmbedder:
    def __init__(self, model="gemini-embedding-001"):
        self.model, self.name = model, f"gemini:{model}"

    def embed(self, texts):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:batchEmbedContents"
        reqs = [{"model": f"models/{self.model}", "content": {"parts": [{"text": t}]}} for t in texts]
        d = _post(url, {"x-goog-api-key": os.environ["GEMINI_API_KEY"]}, {"requests": reqs})
        return [_norm(e["values"]) for e in d["embeddings"]]


def get_embedder(name: str | None = None):
    name = (name or os.getenv("EMBEDDER") or "hash").lower()
    if name == "hash":
        return HashEmbedder()
    if name == "openai":
        return OpenAIEmbedder()
    if name == "gemini":
        return GeminiEmbedder()
    raise ValueError("EMBEDDER must be hash|openai|gemini (Anthropic has no embeddings API; pair Claude with Voyage/OpenAI/Gemini embeddings)")
