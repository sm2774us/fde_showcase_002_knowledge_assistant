import re

STOP = set("a an and are as at be by can do does for from how i if in is it of on or our so that the their there this to was we what when where which who why will with you your about after all any been has have into not than then they them us should would could may".split())


def stem(w: str) -> str:
    for suf in ("ations", "ation", "ings", "ing", "ies", "ed", "es", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[: -len(suf)] + ("y" if suf == "ies" else "")
    return w


def tokens(s: str, keep_stop: bool = False) -> list[str]:
    s = re.sub(r"'s\b", "", s)
    ws = re.findall(r"[a-z0-9$%][a-z0-9_\-\.]*[a-z0-9%]|[a-z0-9]", s.lower())
    return [stem(w) for w in ws if keep_stop or w not in STOP]
