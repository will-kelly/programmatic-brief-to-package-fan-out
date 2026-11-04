"""The refresh cycle. Staleness is a property of claims, not pages.

Every published page records, per claim, the docs section it cites and that
section's hash at check time. When a new docs snapshot lands, a changed
hash flags exactly the claims that depend on that section, and the page
they sit on. A page with 14 claims where one moved gets a one-claim
recheck, not a rewrite. A page that nobody's docs change touched stays
off the queue however old it is.
"""

from __future__ import annotations

from . import factcheck
from .common import load_toml


def queue(catalog: dict, snap: dict, use_model: bool = True) -> dict:
    secs = snap["sections"]
    facts = load_toml("facts.toml")["fact"]
    pages = []
    for slug, p in catalog.get("pages", {}).items():
        flagged = []
        for c in p["claims"]:
            src = c.get("source")
            if not src:
                continue
            if src not in secs:
                flagged.append({**c, "change": "section-removed", "recheck": {"verdict": "unsourced", "reason": "cited section no longer exists"}})
            elif c.get("source_sha") and secs[src]["sha"] != c["source_sha"]:
                r = factcheck.check_claim(c, snap, facts, use_model)
                flagged.append({**c, "change": "section-changed", "new_text": secs[src]["text"],
                                "recheck": {"verdict": r["verdict"], "reason": r.get("reason", "")}})
        if flagged:
            broken = sum(f["recheck"]["verdict"] != "supported" for f in flagged)
            pages.append({"page": slug, "title": p.get("title"), "claims_total": len(p["claims"]),
                          "flagged": flagged, "broken": broken,
                          "priority": "now" if broken else "confirm"})
    pages.sort(key=lambda d: (d["priority"] != "now", -d["broken"]))
    return {"snapshot_id": snap["snapshot_id"], "pages": pages,
            "pages_checked": len(catalog.get("pages", {})),
            "facts_missing_source": [f["id"] for f in facts if f.get("source") not in secs]}


def render_md(q: dict) -> str:
    L = ["# Refresh queue", "", f"Docs snapshot {q['snapshot_id']}. {q['pages_checked']} published pages checked, "
         f"{len(q['pages'])} have claims whose docs section changed.", ""]
    if not q["pages"]:
        L += ["Nothing to do. No published claim depends on a section that changed.", ""]
    for p in q["pages"]:
        L += [f"## {p['title'] or p['page']} ({p['priority']})", "",
              f"{len(p['flagged'])} of {p['claims_total']} claims touch changed docs; {p['broken']} no longer hold.", ""]
        for f in p["flagged"]:
            L += [f"- **{f['id']}** {f['statement']}", f"  - {f['change']} in `{f['source']}`: {f['recheck']['verdict']}. {f['recheck']['reason']}"]
            if f.get("new_text"):
                L += [f"  - docs now say: {f['new_text'][:240]}"]
        L.append("")
    if q["facts_missing_source"]:
        L += ["## Registry facts with no live section", "", "These facts cite a docs section that isn't in the snapshot. Fix the source or retire the fact.", ""]
        L += [f"- {f}" for f in q["facts_missing_source"]] + [""]
    return "\n".join(L)
