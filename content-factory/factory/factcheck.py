"""Fact-check a draft against the docs snapshot, claim by claim.

A draft carries a claims ledger in an HTML comment at the end:

    <!-- claims
    C1 | Free web services spin down after 15 minutes without traffic. | free#spin-down
    -->

and tags the copy with [C1] where the claim is made. Drafts that arrive
without a ledger (partner submissions, old pages) get one extracted first.

Each claim gets one verdict and one tier:

  verdict   supported | contradicted | unsupported | unsourced
  tier      VERIFIED      the cited docs section supports it
            CORROBORATED  only a seed registry fact supports it
            SIGNAL        nothing checkable supports it; a human decides

Checks run cheapest first. A claim that fails a deterministic check never
reaches the model judge, so the judge's cost scales with the claims that
are actually ambiguous.
"""

from __future__ import annotations

import re

from . import llm
from .common import extract_json, load_toml

CLAIMS_BLOCK = re.compile(r"<!--\s*claims\s*\n(.*?)-->", re.S)
TAG_RE = re.compile(r"\[(C\d+)\]")
NUM_RE = re.compile(r"(?<![\w.#-])\$?\d+(?:\.\d+)?(?:%| ?(?:minutes?|seconds?|days?|hours?|GB|MB|instances?))?")
CAPABILITY_RE = re.compile(r"\bRender (?:can|can't|cannot|doesn't|does not|supports?|runs?|offers?|includes?|lets|gives|is|has)\b")

JUDGE_SYSTEM = """You check one claim from a technical article against documentation excerpts.
Answer with JSON only: {"verdict": "supported" | "contradicted" | "unsupported", "reason": "<one sentence>"}
- supported: the evidence states it or directly implies it.
- contradicted: the evidence says something incompatible (a different number, limit, name, or behavior).
- unsupported: the evidence doesn't address it.
Be strict about numbers, plan names, and absolute words like "always", "never", "any"."""

EXTRACT_SYSTEM = """You extract checkable claims about Render (the cloud platform) from a technical article.
A claim is a sentence asserting a fact about Render: a feature, limit, default, behavior, name, or command. Skip opinions and advice.
Reply with a JSON array: [{"id": "C1", "statement": "<the claim>", "quote": "<exact sentence from the article>"}]"""


def parse_claims(md: str) -> list[dict]:
    m = CLAIMS_BLOCK.search(md)
    if not m:
        return []
    out = []
    for line in m.group(1).strip().splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 2 and re.fullmatch(r"C\d+", parts[0]):
            out.append({"id": parts[0], "statement": parts[1],
                        "source": parts[2] if len(parts) > 2 and parts[2] else None})
    return out


def body_of(md: str) -> str:
    return CLAIMS_BLOCK.sub("", md)


def extract(md: str, snap: dict) -> list[dict]:
    from .docs import search
    r = llm.ask(body_of(md), EXTRACT_SYSTEM, role="claim-extract")
    try:
        rows = extract_json(r.text)
    except ValueError:
        return []
    for c in rows:
        # No writer told us the source, so give the judge the top three
        # candidate sections rather than betting on one.
        hits = search(snap, c["statement"], k=3)
        c["source"] = hits[0][0] if hits else None
        c["alt_sources"] = [h[0] for h in hits[1:]]
        c["extracted"] = True
    return rows


def nums(text: str) -> set[str]:
    return {re.sub(r"\s+", " ", n.strip().lower()).rstrip("s") for n in NUM_RE.findall(text)}


def bare(n: str) -> str:
    return re.match(r"\$?\d+(?:\.\d+)?%?", n).group(0)


def check_claim(c: dict, snap: dict, facts: list[dict], use_model: bool = True) -> dict:
    secs = snap["sections"]
    src = c.get("source")
    res = {**c, "checks": []}
    stmt = c["statement"]

    for f in facts:
        for p in f.get("wrong_patterns", []):
            if re.search(p, stmt, re.I):
                ev = secs[src]["text"] if src in secs else f["statement"]
                return {**res, "verdict": "contradicted", "tier": "SIGNAL", "by": "registry-pattern",
                        "reason": f"matches a known-wrong pattern for {f['id']}: {f['statement']}",
                        "evidence": ev, "evidence_sha": secs[src]["sha"] if src in secs else None}

    if not src or src not in secs:
        return {**res, "verdict": "unsourced", "tier": "SIGNAL", "by": "source-lookup",
                "reason": f"cited section '{src}' isn't in the docs snapshot" if src else "no source cited",
                "evidence": None}
    ev = secs[src]["text"]
    for alt in c.get("alt_sources", []):
        if alt in secs:
            ev += f"\n\n({alt}) " + secs[alt]["text"]
    res["evidence"] = ev
    res["evidence_sha"] = secs[src]["sha"]

    claim_nums = {bare(n) for n in nums(stmt)}
    ev_nums = {bare(n) for n in nums(ev)}
    missing = sorted(claim_nums - ev_nums)
    if missing and ev_nums:
        return {**res, "verdict": "contradicted", "tier": "SIGNAL", "by": "figure-match",
                "reason": f"figure {', '.join(missing)} isn't in {src}, which gives {', '.join(sorted(ev_nums))}"}

    if not use_model:
        return {**res, "verdict": "unsupported", "tier": "SIGNAL", "by": "skipped-model", "reason": "model judge off"}
    r = llm.ask(f"CLAIM\n{stmt}\n\nEVIDENCE ({src})\n{ev}", JUDGE_SYSTEM, role="claim-judge")
    try:
        j = extract_json(r.text)
    except ValueError:
        j = {"verdict": "unsupported", "reason": "judge reply unreadable"}
    verdict = j.get("verdict", "unsupported")
    tier = "VERIFIED" if verdict == "supported" else "SIGNAL"
    if verdict == "supported" and snap.get("fixture"):
        # Evidence from the synthetic fixture isn't the live docs.
        tier = "CORROBORATED"
    return {**res, "verdict": verdict, "tier": tier, "by": "model-judge", "reason": j.get("reason", "")}


def untracked(md: str) -> list[str]:
    """Sentences that look like Render claims but carry no [Cn] tag."""
    out = []
    text = body_of(md)
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"(?s)^---.*?---", "", text)
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    merged: list[str] = []
    for part in parts:
        # "...cron jobs. [C2]" splits after the period; the tag belongs to
        # the sentence before it.
        if merged and re.match(r"\s*\[C\d+\]", part):
            merged[-1] += " " + part
        else:
            merged.append(part)
    for sent in merged:
        s = sent.strip().lstrip("-* ").strip()
        if not s or s.startswith(("#", "|")) or TAG_RE.search(s) or "[[TK:" in s:
            continue
        if CAPABILITY_RE.search(s) or (NUM_RE.search(s) and "Render" in s):
            out.append(s[:200])
    return out


def run(md: str, snap: dict, use_model: bool = True) -> dict:
    facts = load_toml("facts.toml")["fact"]
    claims = parse_claims(md)
    extracted = False
    if not claims:
        claims = extract(md, snap)
        extracted = True
    tags = set(TAG_RE.findall(body_of(md)))
    results = [check_claim(c, snap, facts, use_model) for c in claims]
    for r in results:
        if not extracted and r["id"] not in tags:
            r.setdefault("notes", []).append("in the ledger but never tagged in the copy")
    by_tier = {t: sum(r["tier"] == t for r in results) for t in ("VERIFIED", "CORROBORATED", "SIGNAL")}
    return {
        "claims": results,
        "extracted_ledger": extracted,
        "dangling_tags": sorted(tags - {c["id"] for c in claims}),
        "tks": re.findall(r"\[\[TK:\s*([^\]]+)\]\]", body_of(md)),
        "untracked": [] if extracted else untracked(md),
        "counts": by_tier,
        "contradicted": sum(r["verdict"] == "contradicted" for r in results),
        "auto_verified_rate": by_tier["VERIFIED"] / max(len(results), 1),
    }
