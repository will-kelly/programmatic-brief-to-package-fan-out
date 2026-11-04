"""Evals for the factory's own judgment. A change to a prompt, a pattern,
or a model is a change to what the factory lets through, so it gets
measured before it ships.

Suites:
  factcheck  drafts with planted errors; did the checker flag exactly
             the contradicted claims?
  lint       drafts with planted style and structure faults
  brands     answer snippets; did mention detection get the brands right
             (the verb "render" is the classic false positive)?

Cases live in evals/cases/. Reviewer corrections the checker missed land
there too (`cf review done --escaped`), so the suite grows from real misses.
"""

from __future__ import annotations

import json
from pathlib import Path

from . import docs, factcheck, lint
from .brands import Brands
from .common import ROOT, read_json, read_jsonl, write_json

CASES = ROOT / "evals" / "cases"
import os
BASELINE = Path(os.environ.get("CF_BASELINE", ROOT / "evals" / "baseline.json"))


def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 1.0
    r = tp / (tp + fn) if tp + fn else 1.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": round(p, 3), "recall": round(r, 3)}


def run(snap: dict, use_model: bool = True) -> dict:
    fc_tp = fc_fp = fc_fn = 0
    li_tp = li_fp = li_fn = 0
    misses = []
    fields = lint.blueprint_fields(snap)
    for case in sorted(CASES.glob("*.md")):
        md = case.read_text(encoding="utf-8")
        fm = lint.frontmatter(md)
        want_bad = {x.strip() for x in fm.get("expect_flagged", "").split(",") if x.strip()}
        res = factcheck.run(md, snap, use_model)
        got_bad = {c["id"] for c in res["claims"] if c["verdict"] in ("contradicted", "unsourced")}
        fc_tp += len(want_bad & got_bad); fc_fp += len(got_bad - want_bad); fc_fn += len(want_bad - got_bad)
        for x in sorted(want_bad - got_bad):
            misses.append(f"{case.name}: factcheck missed {x}")
        for x in sorted(got_bad - want_bad):
            misses.append(f"{case.name}: factcheck wrongly flagged {x}")
        want_rules = {x.strip() for x in fm.get("expect_lint", "").split(",") if x.strip()}
        got_rules = {i["rule"] for i in lint.run(md, fm.get("format"), fields) if i["severity"] == "error"}
        li_tp += len(want_rules & got_rules); li_fp += len(got_rules - want_rules); li_fn += len(want_rules - got_rules)
        for x in sorted(want_rules - got_rules):
            misses.append(f"{case.name}: lint missed {x}")
        for x in sorted(got_rules - want_rules):
            misses.append(f"{case.name}: lint wrongly raised {x}")

    br = Brands()
    b_tp = b_fp = b_fn = 0
    for row in read_jsonl(CASES / "brands.jsonl"):
        got = set(m["brand"] for m in br.mentions(row["text"]))
        want = set(row["expect"])
        b_tp += len(got & want); b_fp += len(got - want); b_fn += len(want - got)
        for x in sorted(want - got):
            misses.append(f"brands: missed {x} in {row['text'][:50]!r}")
        for x in sorted(got - want):
            misses.append(f"brands: false {x} in {row['text'][:50]!r}")

    return {"factcheck": prf(fc_tp, fc_fp, fc_fn), "lint": prf(li_tp, li_fp, li_fn),
            "brands": prf(b_tp, b_fp, b_fn), "misses": misses, "model_judge": use_model}


def mode(use_model: bool) -> str:
    """Baselines are per judge mode: a fake judge, no judge, and a real
    model judge catch different things and shouldn't be compared."""
    import os
    return f"{os.environ.get('CF_LLM', 'claude-cli')}:{'judge' if use_model else 'no-judge'}"


def compare(cur: dict, base: dict | None) -> list[str]:
    if not base:
        return []
    regress = []
    for suite in ("factcheck", "lint", "brands"):
        for m in ("precision", "recall"):
            if cur[suite][m] < base[suite][m] - 1e-9:
                regress.append(f"{suite} {m} fell from {base[suite][m]} to {cur[suite][m]}")
    return regress


def render(cur: dict, base: dict | None, regress: list[str]) -> str:
    L = ["suite       precision  recall   (baseline)"]
    for s in ("factcheck", "lint", "brands"):
        b = f"({base[s]['precision']}, {base[s]['recall']})" if base else ""
        L.append(f"{s:<11} {cur[s]['precision']:<10} {cur[s]['recall']:<8} {b}")
    if cur["misses"]:
        L += ["", "misses:"] + [f"  - {m}" for m in cur["misses"]]
    L += ["", "REGRESSION: " + "; ".join(regress) if regress else "no regression against baseline"]
    return "\n".join(L)
