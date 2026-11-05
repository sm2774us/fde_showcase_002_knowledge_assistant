"""Access control + prompt-injection defenses. Retrieved text is DATA, never instructions."""
from __future__ import annotations

import re

ROLES = {
    "public": {"public"},
    "employee": {"public", "internal"},
    "security": {"public", "internal", "restricted:security"},
    "hr": {"public", "internal", "restricted:hr"},
}

INJECTION = [re.compile(p, re.I) for p in (
    r"ignore (all |any )?(previous|prior|above) (instructions|prompts?)",
    r"disregard (the |all )?(previous|prior|above|system)",
    r"you are now (in )?\w+ mode",
    r"(reveal|print|show|leak) (the |your )?(system prompt|hidden|restricted|secret)",
    r"https?://\S+/(collect|exfil)",
    r"\bsend (it|them|this)? ?to https?://",
)]


def allowed(role: str, access: str) -> bool:
    if role not in ROLES:
        raise ValueError(f"unknown role '{role}'. Roles: {', '.join(ROLES)}")
    return access in ROLES[role]


def looks_like_injection(text: str) -> bool:
    return any(p.search(text) for p in INJECTION)


def sanitize(text: str) -> tuple[str, int]:
    """Drop lines/sentences that look like instructions aimed at the model. Returns (clean_text, n_removed)."""
    removed, out = 0, []
    for line in text.splitlines():
        parts = re.split(r"(?<=[.!?])\s+", line)
        keep = [p for p in parts if not looks_like_injection(p)]
        removed += len(parts) - len(keep)
        out.append(" ".join(keep))
    return "\n".join(out), removed
