"""The scorecard. Volume published is one row of it, not the headline.

Visibility   unbranded mention rate and first-pick rate, by survey, with
             intervals, overall and for the clusters the plan targets
Accuracy     answers with wrong claims about Render; contradicted claims
             caught before publishing; escaped errors found in review
Review cost  estimated and actual expert minutes per piece; share of
             claims auto-verified
Freshness    published claims whose docs section changed and are unrechecked
Spend        model cost per piece and per survey
"""

from __future__ import annotations

from pathlib import Path

from .common import STATE, pct, read_json, read_jsonl


def scorecard(target_clusters: list[str] | None = None) -> str:
    surveys = []
    for d in sorted((STATE / "surveys").glob("*/summary.json")) if (STATE / "surveys").exists() else []:
        surveys.append(read_json(d))
    latest = STATE / "surveys" / "LATEST"
    if latest.exists():
        p = Path(latest.read_text().strip()) / "summary.json"
        if p.exists() and all(s["survey_id"] != read_json(p)["survey_id"] for s in surveys):
            surveys.append(read_json(p))
    surveys.sort(key=lambda s: s["survey_id"])
    checks = read_jsonl(STATE / "checks.jsonl")
    reviews = read_jsonl(STATE / "reviews.jsonl")
    calls = read_jsonl(STATE / "llm-calls.jsonl")
    cat = read_json(STATE / "catalog.json", {"pages": {}})
    rq = read_json(STATE / "refresh-queue.json", {"pages": []})

    L = ["# Content factory scorecard", ""]
    L += ["## Visibility in answers", ""]
    if surveys:
        L += ["| Survey | Unbranded answers | Mentioned | 95% CI | Picked first | Wrong about Render (firm / disputed) | Registry coverage |", "|---|---|---|---|---|---|---|"]
        for s in surveys:
            L.append(f"| {s['date']} ({', '.join(s['engines'])}) | {s['unbranded_answers']} | {pct(s['mention_rate'])} | "
                     f"{pct(s['mention_ci'][0])}–{pct(s['mention_ci'][1])} | {pct(s['first_pick_rate'])} | "
                     f"{s.get('answers_with_pattern_wrong', 0)} / {s['answers_with_wrong_claims'] - s.get('answers_with_pattern_wrong', 0)} of {s['answers']} | "
                     f"{pct(s.get('registry_coverage', 0))} |")
        if target_clusters:
            s = surveys[-1]
            L += ["", "Target clusters in the latest survey:", ""]
            for c in target_clusters:
                cl = s["clusters"].get(c)
                if cl and cl["mention_rate"] is not None:
                    L.append(f"- {c}: {pct(cl['mention_rate'])} (95% CI {pct(cl['ci'][0])}–{pct(cl['ci'][1])})")
        L += ["", "A move between surveys counts only when the intervals stop overlapping. Anything else is sampling noise. "
              "Firm means a known-wrong pattern or a human confirmed it; disputed means only the model judge flagged it.", ""]
    else:
        L += ["No surveys yet.", ""]

    L += ["## Accuracy and review cost", ""]
    if checks:
        n = len(checks)
        claims = sum(c["claims"] for c in checks)
        L += [f"- {n} drafts checked ({sum(c['source'] != 'in-house' for c in checks)} from partners), {claims} claims",
              f"- {sum(c['contradicted'] for c in checks)} contradicted claims caught before publishing",
              f"- auto-verified share of claims: {pct(sum(c.get('tier_verified', 0) for c in checks) / max(claims, 1))} "
              f"(corroborated against a fixture or seed facts: {pct(sum(c.get('tier_corroborated', 0) for c in checks) / max(claims, 1))})",
              f"- estimated expert review: {sum(c['estimated_minutes'] for c in checks) / n:.1f} min per piece "
              f"(vs {sum(c['unassisted_minutes'] for c in checks) / n:.1f} unassisted). Both are the time model in pipeline.py until `cf review done` records real minutes."]
    if reviews:
        mins = [r["minutes"] for r in reviews]
        L += [f"- actual expert review: {sum(mins) / len(mins):.1f} min per piece over {len(reviews)} reviews",
              f"- escaped errors (reviewer caught, checker passed): {sum(r.get('escaped', 0) for r in reviews)}"]
    if not checks and not reviews:
        L += ["No drafts checked yet."]
    L += [""]

    L += ["## Catalog and freshness", "",
          f"- {len(cat['pages'])} published pages, {sum(len(p['claims']) for p in cat['pages'].values())} tracked claims",
          f"- {sum(len(p['flagged']) for p in rq['pages'])} claims on the refresh queue, {sum(p['broken'] for p in rq['pages'])} no longer hold", ""]

    L += ["## Spend", ""]
    by_role: dict[str, float] = {}
    for c in calls:
        by_role[c["role"]] = by_role.get(c["role"], 0) + c["cost_usd"]
    L += [f"- {r}: ${v:.2f}" for r, v in sorted(by_role.items(), key=lambda kv: -kv[1])] or ["- none recorded"]
    L += ["", "## Partners", ""]
    partners: dict[str, list] = {}
    for c in checks:
        if c["source"] != "in-house":
            partners.setdefault(c["source"], []).append(c)
    if partners:
        L += ["| Partner | Drafts | Ready on first check | Contradicted per draft | Lint errors per draft |", "|---|---|---|---|---|"]
        for p, cs in sorted(partners.items()):
            L.append(f"| {p} | {len(cs)} | {pct(sum(c['status'] != 'blocked' for c in cs) / len(cs))} | "
                     f"{sum(c['contradicted'] for c in cs) / len(cs):.1f} | {sum(c['lint_errors'] for c in cs) / len(cs):.1f} |")
    else:
        L += ["No partner drafts yet."]
    L += ["", "Signups attributed to content aren't in this scorecard until there's a join between page views and signup source. Don't fake that number.", ""]
    return "\n".join(L)
