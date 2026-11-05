"""Heading-aware, table-aware chunking. A markdown table is an atomic block: never severed mid-table."""
from __future__ import annotations

import pathlib
import re
from dataclasses import dataclass, asdict


@dataclass
class Chunk:
    id: str
    doc_id: str
    title: str
    heading: str
    text: str
    access: str
    owner: str

    def to_dict(self):
        return asdict(self)


def parse_front_matter(raw: str) -> tuple[dict, str]:
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
    if not m:
        return {}, raw
    meta = dict(l.split(":", 1) for l in m.group(1).splitlines() if ":" in l)
    return {k.strip(): v.strip() for k, v in meta.items()}, m.group(2)


def _blocks(body: str):
    """Yield (heading, block_text); tables and paragraphs are atomic blocks."""
    heading, buf, kind = "", [], None
    out = []

    def flush():
        nonlocal buf, kind
        if buf:
            out.append((heading, "\n".join(buf).strip()))
        buf, kind = [], None

    for line in body.splitlines():
        if re.match(r"^#{1,6}\s", line):
            flush()
            heading = line.lstrip("# ").strip()
            continue
        is_tbl = line.lstrip().startswith("|")
        if not line.strip():
            flush()
            continue
        if buf and (is_tbl != (kind == "table")):
            flush()
        kind = "table" if is_tbl else "para"
        buf.append(line)
    flush()
    return out


def chunk_document(path: pathlib.Path, max_chars: int = 700) -> list[Chunk]:
    meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
    doc_id, title = path.stem, meta.get("title", path.stem)
    chunks: list[Chunk] = []
    cur_head, cur = None, ""

    def emit(head, text):
        if text.strip():
            n = len(chunks) + 1
            chunks.append(Chunk(f"{doc_id}#{n}", doc_id, title, head, text.strip(), meta.get("access", "internal"), meta.get("owner", "")))

    for head, block in _blocks(body):
        if cur_head is not None and (head != cur_head or len(cur) + len(block) > max_chars):
            emit(cur_head, cur)
            cur = ""
        cur_head = head
        cur += ("\n\n" if cur else "") + block   # an oversized table stays whole by design
    if cur_head is not None:
        emit(cur_head, cur)
    return chunks


def chunk_corpus(directory: str | pathlib.Path) -> list[Chunk]:
    out: list[Chunk] = []
    for p in sorted(pathlib.Path(directory).glob("*.md")):
        out += chunk_document(p)
    return out
