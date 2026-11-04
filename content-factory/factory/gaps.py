"""Gap analysis: turn survey, citation, traffic, and catalog signals into a
diagnosis per question, then a ranked backlog.

The diagnosis comes first because each kind of gap has a different fix,
and most of them aren't "publish another article":

  WRONG        answers say something false about Render. Misinformation
               compounds: every wrong answer gets repeated and trained on.
               Fix the docs page that states it, then the pages that echo it.
  DISPUTED     only the model judge says an answer is wrong. Nobody ships a
               correction on a model's say-so: a human confirms first.
  ABSENT       Render isn't in the answer; competitors are. Needs a page
               that answers the question, in the shape answer engines lift.
  BURIED       Render is named but late, or rarely picked first. Needs a
               sharper, more specific page, often a stack guide.
  OUT-CITED    Render is named, but someone else's URL is the source.
               Needs a page worth citing on exactly this question.
  UNRETRIEVED  We already have a page aimed here, but index and live-fetch
               agents aren't reaching it. Fix discoverability (llms.txt,
               markdown twin, internal links, robots), not content.
  HOLDING      Render is mentioned and picked. Watch it; don't spend on it.
"""

from __future__ import annotations

from collections import defaultdict

from .brands import Brands
from .common import pct

SEVERITY = {"WRONG": 5, "DISPUTED": 2, "ABSENT": 4, "UNRETRIEVED": 3, "OUT-CITED": 3, "BURIED": 2, "HOLDING": 0}
EFFORT = {"docs": 1.0, "discoverability": 0.5, "use-case": 2.0, "stack-guide": 1.5, "comparison": 2.5}
FIX = {
    "WRONG": "Correct the source of truth: the docs section and fact registry entry, then refresh pages that repeat it.",
    "DISPUTED": "A reviewer reads the flagged answers against the live docs. If the answer is right, the registry has a gap: add the fact. If it's wrong, it becomes a WRONG item.",
    "ABSENT": "Write the page that answers this question directly, answer-first, with a concede section.",
    "BURIED": "Make the existing coverage more specific to this stack or use case so Render is the concrete pick.",
    "OUT-CITED": "Publish the page that third parties are being cited for; match their depth on this exact question.",
    "UNRETRIEVED": "Fix discoverability first: llms.txt entry, markdown twin, internal links from docs, robots rules.",
    "HOLDING": "No work. Keep it in the survey.",
}


def diagnose(q: dict, catalog: dict, traffic: dict, cites: list[dict], brands: Brands) -> dict:
    qid = q["question_id"]
    pages = [slug for slug, p in catalog.get("pages", {}).items() if qid in p.get("target_questions", [])]
    hits = {"index": 0, "live-fetch": 0, "training": 0, "agent": 0}
    for slug in pages:
        for cls, n in traffic.get("by_path", {}).get("/" + slug, {}).items():
            hits[cls] = hits.get(cls, 0) + n
    q_cites = [c for c in cites if c["question_id"] == qid]
    owners = defaultdict(int)
    for c in q_cites:
        owners[brands.owner(c["cited_url"])] += 1
    for o, n in q.get("citation_owners", {}).items():
        owners[o] += n
    ours = owners.get(brands.us, 0)
    lo, hi = q["ci"]
    evidence = [f"mentioned in {pct(q['mention_rate'])} of {q['n']} answers (95% CI {pct(lo)}–{pct(hi)})"]
    if q["top_competitors"]:
        evidence.append("named instead: " + ", ".join(f"{b} ({n}/{q['n']})" for b, n in q["top_competitors"][:3]))

    firm_wrong = [c for c in q["wrong_claims"] if c.get("by") in ("pattern", "human")]
    if firm_wrong:
        kind = "WRONG"
        evidence.append(f"{len(firm_wrong)} wrong claims, e.g. \"{firm_wrong[0]['claim'][:90]}\" vs {firm_wrong[0].get('fact_id')}")
    elif q["wrong_claims"] and q.get("branded"):
        kind = "DISPUTED"
        evidence.append(f"model judge flagged \"{q['wrong_claims'][0]['claim'][:90]}\" against {q['wrong_claims'][0].get('fact_id')}")
    elif pages and hits["index"] + hits["live-fetch"] == 0:
        kind = "UNRETRIEVED"
        evidence.append(f"page {pages[0]} targets this but logged 0 index or live-fetch hits")
    elif q.get("branded"):
        kind = "HOLDING"
    elif q["mention_rate"] < 1 / 3:
        kind = "ABSENT"
        if q["avg_brands_named"] == 0:
            evidence.append("no platform named at all: answers treat this as a tooling question, so the page has to make the platform part of the answer")
    elif sum(owners.values()) and ours == 0:
        kind = "OUT-CITED"
        top = sorted(owners.items(), key=lambda kv: -kv[1])[:2]
        evidence.append("cited instead: " + ", ".join(f"{o} ({n})" for o, n in top))
    elif q["first_pick_rate"] < 0.34 or (q["avg_rank"] or 9) >= 3:
        kind = "BURIED"
        evidence.append(f"picked first in {pct(q['first_pick_rate'])}, average rank {q['avg_rank']}")
    else:
        kind = "HOLDING"
    if hits["live-fetch"]:
        evidence.append(f"{hits['live-fetch']} live-fetch hits on our page")
    # Three samples can't separate 0% from 50%. Say so instead of
    # pretending; the next survey should sample this question harder.
    confidence = "firm" if (kind == "ABSENT" and hi < 0.5) or (kind != "ABSENT" and q["n"] >= 5) or kind in ("WRONG", "DISPUTED") else "tentative"
    if confidence == "tentative":
        evidence.append(f"tentative on {q['n']} samples: raise k for this question next survey")
    return {"question_id": qid, "kind": kind, "confidence": confidence, "pages": pages, "evidence": evidence,
            "agent_hits": hits, "owners": dict(owners)}


def backlog(survey: dict, questions: list[dict], catalog: dict, traffic: dict, cites: list[dict]) -> dict:
    brands = Brands()
    qmeta = {q["id"]: q for q in questions}
    diag = [diagnose(q, catalog, traffic, cites, brands) for q in survey["questions"]]

    # One piece of content usually answers several questions. Group by
    # (fix type, cluster, format) so the backlog is pieces, not questions.
    items: dict[tuple, dict] = {}
    for d in diag:
        if d["kind"] == "HOLDING":
            continue
        q = qmeta.get(d["question_id"], {})
        fmt = "docs" if d["kind"] in ("WRONG", "DISPUTED") else ("discoverability" if d["kind"] == "UNRETRIEVED" else q.get("format", "use-case"))
        key = (d["kind"], q.get("cluster", "?"), fmt)
        it = items.setdefault(key, {"kind": d["kind"], "cluster": key[1], "format": fmt, "questions": [], "evidence": [], "demand": 0})
        it["questions"].append(d["question_id"])
        it["demand"] += q.get("demand", 1)
        it["evidence"].append(f"`{d['question_id']}`: " + "; ".join(d["evidence"]))

    out = []
    for it in items.values():
        sev = SEVERITY[it["kind"]]
        effort = EFFORT.get(it["format"], 2.0)
        score = round(it["demand"] * sev / effort, 1)
        it.update({
            "score": score, "severity": sev, "effort": effort, "fix": FIX[it["kind"]],
            "why": (f"{it['kind']} on {len(it['questions'])} question(s) in {it['cluster']}, combined demand {it['demand']}; "
                    f"severity {sev} x demand / effort {effort} = {score}."),
            "title": title_for(it, qmeta),
        })
        out.append(it)
    out.sort(key=lambda d: -d["score"])
    counts = defaultdict(int)
    for d in diag:
        counts[d["kind"]] += 1
    return {"items": out, "diagnosis": diag, "counts": dict(counts)}


def title_for(it: dict, qmeta: dict) -> str:
    ranked = sorted((q for q in it["questions"] if q in qmeta), key=lambda q: -qmeta[q].get("demand", 1))
    texts = [qmeta[q]["text"] for q in ranked]
    lead = texts[0].rstrip("?") if texts else it["cluster"]
    return {"WRONG": f"Correct: {lead}", "DISPUTED": f"Confirm or add to registry: {lead}", "UNRETRIEVED": f"Make findable: {lead}"}.get(it["kind"], lead)


def render_md(b: dict, survey_meta: str) -> str:
    L = ["# Content backlog", "", survey_meta, "",
         "Diagnosis across the question set: " + ", ".join(f"{k} {v}" for k, v in sorted(b["counts"].items(), key=lambda kv: -SEVERITY[kv[0]])) + ".", "",
         "Score is severity × demand ÷ effort. Severity puts wrong answers first, because a wrong answer about Render does more damage than a missing one and gets repeated. Effort favors fixes that move several questions at once.", "",
         "| # | Score | Type | Piece | Format | Questions |", "|---|---|---|---|---|---|"]
    for i, it in enumerate(b["items"], 1):
        L.append(f"| {i} | {it['score']} | {it['kind']} | {it['title']} | {it['format']} | {len(it['questions'])} |")
    L += ["", "## Why each one ranks where it does", ""]
    for i, it in enumerate(b["items"], 1):
        L += [f"### {i}. {it['title']}", "", f"{it['why']} {it['fix']}", ""] + [f"- {e}" for e in it["evidence"]] + [""]
    return "\n".join(L)
