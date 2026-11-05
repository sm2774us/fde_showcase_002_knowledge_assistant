"""python -m knowledge_assistant ingest|ask|eval|serve"""
from __future__ import annotations

import argparse
import json
import sys

from .assistant import ask
from .index import HybridIndex
from .llm import LLMError, get_llm
from .security import ROLES

INDEX = ".index/index.json"
AUDIT = ".index/audit.jsonl"


def load_index(embedder=None) -> HybridIndex:
    try:
        return HybridIndex.load(INDEX, embedder)
    except FileNotFoundError:
        ix = HybridIndex.build("corpus", embedder)
        ix.save(INDEX)
        return ix


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="knowledge_assistant")
    sub = p.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("ingest")
    i.add_argument("--corpus", default="corpus")
    i.add_argument("--embedder", default=None, help="hash|openai|gemini")
    a = sub.add_parser("ask")
    a.add_argument("question")
    a.add_argument("--role", default="employee", choices=list(ROLES))
    a.add_argument("--provider", default=None)
    a.add_argument("--model", default=None)
    a.add_argument("--mode", default="hybrid", choices=["hybrid", "bm25", "dense"])
    a.add_argument("--json", action="store_true")
    e = sub.add_parser("eval")
    e.add_argument("--provider", default=None)
    sub.add_parser("serve").add_argument("--port", type=int, default=8081)
    args = p.parse_args(argv)
    try:
        if args.cmd == "ingest":
            ix = HybridIndex.build(args.corpus, args.embedder)
            ix.save(INDEX)
            print(f"indexed {len(ix.chunks)} chunks from {args.corpus} with {ix.embedder.name} -> {INDEX}")
        elif args.cmd == "ask":
            r = ask(args.question, args.role, load_index(), get_llm(args.provider, args.model), mode=args.mode, audit_path=AUDIT)
            if args.json:
                print(json.dumps(r, indent=2))
            else:
                print(("REFUSED: " + r["reason"] + "\n" if r["refused"] else "") + r["answer"])
                for s in r["sources"]:
                    print(f"  [{s['id']}] {s['title']} > {s['section']}")
                print(f"  flags={r['flags']}")
        elif args.cmd == "eval":
            from .evaluate import run
            return run(args.provider)
        elif args.cmd == "serve":
            from .server import serve
            serve(args.port)
    except (LLMError, ValueError) as ex:
        print(f"error: {ex}", file=sys.stderr)
        return 2
    return 0
