"""Lint a draft for the two failure modes that cost citations: prose that
reads machine-made, and structure an agent can't lift an answer from.

Each rule has an ID, a severity, and a reason. Errors block publishing;
warnings go into the review packet.
"""

from __future__ import annotations

import re

from .common import load_toml

FINGERPRINTS = [
    r"\bdelve\b", r"\bleverag(e|es|ing)\b(?! ratio)", r"\butiliz(e|es|ing)\b", r"\brobust\b", r"\bseamless(ly)?\b",
    r"\bpowerful\b", r"\bcomprehensive\b", r"\bholistic\b", r"\bcutting[- ]edge\b", r"\bgame[- ]chang(er|ing)\b",
    r"\bstreamlin(e|es|ed|ing)\b", r"\bempower(s|ing)?\b", r"\bunlock(s|ing)?\b", r"\bdeep dive\b",
    r"in today's (rapidly )?(evolving|fast-paced)", r"\bit's worth noting\b", r"\bat the end of the day\b",
    r"\bmoving forward\b", r"\btapestry\b", r"\blandscape\b", r"\brealm\b", r"\bnavigate the complexit",
    r"\blet's dive in\b", r"\bhere's the thing\b", r"\bin conclusion\b", r"\bnot (just|only) .{1,40}, but\b",
    r"\bwhether you're\b", r"\belevate\b", r"\bsupercharge\b", r"\beffortless(ly)?\b",
]
SUPERLATIVES = r"\b(best|fastest|easiest|cheapest|only platform|most reliable|simplest)\b"
OPENERS = r"^(in this (article|guide|post)|are you|have you ever|when it comes to|if you're looking)"


def rule(rid, sev, msg, where=""):
    return {"rule": rid, "severity": sev, "message": msg, "where": where}


def strip(md):
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)
    return re.sub(r"(?s)^---\n.*?\n---\n", "", md)


def frontmatter(md: str) -> dict:
    m = re.match(r"(?s)^---\n(.*?)\n---\n", md)
    fm = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip()
    return fm


def run(md: str, fmt: str | None = None, doc_fields: set[str] | None = None) -> list[dict]:
    out = []
    fm = frontmatter(md)
    fmt = fmt or fm.get("format", "")
    body = strip(md)
    prose = re.sub(r"```.*?```", "", body, flags=re.S)
    lines = prose.splitlines()

    for pat in FINGERPRINTS:
        for m in re.finditer(pat, prose, re.I):
            out.append(rule("fingerprint", "error", f"machine-sounding phrase '{m.group(0)}'", m.group(0)))
    if prose.count("—") > max(2, len(prose) // 1500):
        out.append(rule("em-dash", "warning", f"{prose.count('—')} em dashes; use commas, colons, or periods"))
    if "!" in re.sub(r"!\[", "", prose):
        out.append(rule("exclamation", "warning", "exclamation point"))
    for m in re.finditer(SUPERLATIVES, prose, re.I):
        sent = next((s.strip() for s in re.split(r"(?<=[.?])\s+|\n+", prose) if m.group(0) in s), "")
        if not re.search(r"\[C\d+\]", sent):
            out.append(rule("untagged-superlative", "warning", f"'{m.group(0)}' with no claim behind it", sent[:120]))

    # Answer-first: the first paragraph after the H1 should answer the
    # question. Agents quote the top of the page; preamble wastes it.
    paras = [p.strip() for p in re.split(r"\n\s*\n", prose) if p.strip() and not p.strip().startswith("#")]
    if paras:
        first = paras[0]
        words = len(first.split())
        if re.search(OPENERS, first, re.I):
            out.append(rule("answer-first", "error", "opens with preamble instead of the answer", first[:100]))
        elif words > 70:
            out.append(rule("answer-first", "warning", f"first paragraph is {words} words; put the answer in the first 60"))

    h2 = [l[3:].strip() for l in lines if l.startswith("## ")]
    if len(h2) >= 3 and sum(h.endswith("?") for h in h2) < len(h2) / 3:
        out.append(rule("question-headings", "warning",
                        "fewer than a third of H2s are phrased as the question a developer would ask"))
    for h in [l.lstrip("# ").strip() for l in lines if re.match(r"^#{1,4} ", l)]:
        words = h.split()
        caps = [w for w in words[1:] if w[:1].isupper() and not re.search(r"[A-Z].*[A-Z]|\d|\.", w)
                and w.lower() not in {"render", "postgres", "docker", "python", "node", "django", "fastapi", "next.js", "redis", "celery", "railway", "heroku", "vercel", "aws", "fly.io", "key", "value", "blueprint", "blueprints", "flask", "rails", "go", "kubernetes", "github", "i"}]
        if len(caps) >= 2:
            out.append(rule("sentence-case", "warning", "heading isn't sentence case", h))

    opening = True
    for m in re.finditer(r"^```(\S*)", body, re.M):
        if opening and not m.group(1):
            out.append(rule("code-lang", "warning", "code block with no language tag"))
        opening = not opening
    if doc_fields:
        for block in re.findall(r"```ya?ml\n(.*?)```", body, re.S):
            if "services:" not in block:
                continue
            for k in re.findall(r"^\s*-?\s*([A-Za-z][A-Za-z0-9]*):", block, re.M):
                if k not in doc_fields:
                    out.append(rule("blueprint-field", "error",
                                    f"render.yaml key '{k}' isn't a field in the Blueprint docs snapshot", k))

    if fmt == "comparison" and not re.search(r"(?im)^##.*(isn't|is not|not) (the )?(right|best|a good) fit|^##.*when (not to|to pick|to choose) ", body):
        out.append(rule("concede", "error",
                        "comparison has no section on when the other option wins. One-sided comparisons read as ads, and answer engines treat them that way."))
    if fmt in ("use-case", "stack-guide") and not re.search(r"(?im)^##.*(isn't|is not|not) (the )?(right|best|a good) fit", body):
        out.append(rule("concede", "warning", "no 'when Render isn't the right fit' section"))
    if "last_verified" not in fm and "verified" not in fm:
        out.append(rule("verified-date", "warning", "no last_verified date in front matter"))
    if not fm.get("target_questions"):
        out.append(rule("targets", "warning", "front matter doesn't list target_questions, so the survey can't measure this page"))
    return out


def blueprint_fields(snap: dict) -> set[str]:
    """The Blueprint keys the docs mention, pulled from backticks in the
    blueprint-spec sections. The linter's allow-list moves with the docs."""
    fields = set()
    for sid, s in snap["sections"].items():
        if sid.startswith("blueprint-spec#"):
            fields |= set(re.findall(r"`([A-Za-z][A-Za-z0-9]*)`", s["text"]))
    return fields | {"key", "value", "fromDatabase", "property", "fromService", "sync", "generateValue", "databaseName", "user"}
