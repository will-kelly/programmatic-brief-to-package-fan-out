"""The content factory pipeline: brief -> research -> draft -> fact-check
-> lint -> review packet -> publish.

Every stage reads and writes plain files in a run directory, so any stage
can be rerun alone, diffed against the last run, or handed to a person.
The same stages run locally (`cf run`) or as Render Workflows tasks
(workflows/render_workflows.py); this module has no idea which.

Partner drafts enter at the fact-check stage (`cf check`) and come out
with the same packet and verdicts as in-house drafts. One quality bar.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from . import docs, factcheck, lint, llm
from .common import (ROOT, STATE, append_jsonl, now_id, read_json, sha, slugify,
                     today, write_json)

# Expert-review time model, in minutes. It starts as a guess; `cf review
# done` records real minutes, and `cf metrics` reports both so the model can
# be recalibrated against what reviewers actually spend.
REVIEW_MIN = {"read": 4.0, "SIGNAL": 2.0, "CORROBORATED": 0.5, "VERIFIED": 0.1, "lint-error": 1.0}


def research(brief: dict, snap: dict, k: int = 6, cap: int = 24) -> dict:
    """Build the source pack: search once for the whole brief and once per
    question, then pull in every section of each page that hit. Docs pages
    are short, and the section that answers a follow-up ("can workers run
    free?") usually sits next to the one that matched. Retrieving sections
    alone missed exactly those (see examples/README.md, run 1 vs run 2)."""
    queries = [" ".join([brief["title"], *brief.get("questions_text", []), brief.get("angle", "")]),
               *brief.get("questions_text", [])]
    scores: dict[str, float] = {}
    for q in queries:
        for sid, sc in docs.search(snap, q, k=k):
            scores[sid] = max(scores.get(sid, 0), sc)
    for extra in brief.get("must_cite", []):
        scores.setdefault(extra, 0.0)
    pages = {snap["sections"][sid]["page"] for sid in scores if sid in snap["sections"]}
    for sid, sec in snap["sections"].items():
        if sec["page"] in pages:
            scores.setdefault(sid, 0.0)
    hits = sorted(scores.items(), key=lambda kv: -kv[1])[:cap]
    pack = [{"n": i + 1, "id": sid, "heading": snap["sections"][sid]["heading"],
             "text": snap["sections"][sid]["text"], "sha": snap["sections"][sid]["sha"], "score": sc}
            for i, (sid, sc) in enumerate(hits)]
    return {"snapshot_id": snap["snapshot_id"], "sections": pack}


def draft(brief: dict, pack: dict) -> tuple[str, float]:
    system = (ROOT / "prompts" / "draft.md").read_text(encoding="utf-8")
    voice = ROOT / "config" / "voice.md"
    if voice.exists():
        system += "\n\n## House voice\n\n" + voice.read_text(encoding="utf-8")
    src = "\n\n".join(f"[{s['n']}] {s['id']} ({s['heading']})\n{s['text']}" for s in pack["sections"])
    msg = (f"BRIEF\n{json.dumps(brief, indent=2)}\n\nTODAY\n{today()}\n\nSOURCE PACK\n{src}")
    r = llm.ask(msg, system, role="draft", timeout=600)
    text = r.text.strip()
    text = re.sub(r"^```(?:markdown|md)?\n(.*)\n```$", r"\1", text, flags=re.S)
    return text + "\n", r.cost_usd


def review_estimate(fc: dict, lint_issues: list[dict]) -> dict:
    mins = REVIEW_MIN["read"]
    for c in fc["claims"]:
        mins += REVIEW_MIN[c["tier"]]
    mins += REVIEW_MIN["lint-error"] * sum(i["severity"] == "error" for i in lint_issues)
    return {"estimated_minutes": round(mins, 1),
            "unassisted_minutes": round(REVIEW_MIN["read"] + 2.0 * len(fc["claims"]) + 6, 1)}


def packet(md_name: str, fc: dict, lint_issues: list[dict], est: dict, brief: dict | None) -> str:
    """What the expert reviewer reads. Everything a machine settled is
    collapsed; everything it couldn't settle is first, with the evidence
    next to it so the reviewer never has to go find the docs page."""
    sig = [c for c in fc["claims"] if c["tier"] == "SIGNAL"]
    cor = [c for c in fc["claims"] if c["tier"] == "CORROBORATED"]
    ver = [c for c in fc["claims"] if c["tier"] == "VERIFIED"]
    errs = [i for i in lint_issues if i["severity"] == "error"]
    warns = [i for i in lint_issues if i["severity"] == "warning"]
    L = [f"# Review packet: {md_name}", ""]
    if brief:
        L += [f"Brief: {brief['title']} ({brief.get('format')}), targets {', '.join(brief.get('questions', []))}", ""]
    L += [f"**{len(sig)} claims need you.** {len(ver)} verified against the docs, {len(cor)} corroborated by seed facts only, "
          f"{len(errs)} lint errors. Estimated review time {est['estimated_minutes']} minutes "
          f"(about {est['unassisted_minutes']} without the checker).", ""]
    if fc.get("tks"):
        L += ["## Open TKs", "", "The writer stopped instead of guessing. Each of these is a fact the docs snapshot doesn't state. They also go to the docs-gap report (`cf docs gaps`).", ""]
        L += [f"- {t}" for t in fc["tks"]] + [""]
    if fc.get("extracted_ledger"):
        L += ["The writer sent no claims ledger, so one was extracted. Check that nothing important is missing from it.", ""]
    if sig:
        L += ["## Decide these", ""]
        for c in sig:
            L += [f"### {c['id']}: {c['verdict']}", "", f"> {c['statement']}", "",
                  f"Why flagged: {c.get('reason', '')} (by {c.get('by')})", ""]
            if c.get("evidence"):
                L += [f"Docs say ({c.get('source')}):", "", "> " + c["evidence"].replace("\n", "\n> "), ""]
            L += ["- [ ] Correct as written   - [ ] Fix copy   - [ ] Fix docs or registry", ""]
    if fc["untracked"]:
        L += ["## Untracked claims", "", "These sentences read like claims about Render but carry no claim tag, so nothing checked them.", ""]
        L += [f"- {u}" for u in fc["untracked"]] + [""]
    if errs or warns:
        L += ["## Lint", ""]
        L += [f"- **{i['rule']}** ({i['severity']}): {i['message']}" + (f" — `{i['where'][:80]}`" if i['where'] else "") for i in errs + warns] + [""]
    if cor:
        L += ["## Corroborated only (spot-check one)", ""] + [f"- {c['id']}: {c['statement']} ({c.get('source')})" for c in cor] + [""]
    if ver:
        L += ["<details><summary>Verified against the docs ({})</summary>".format(len(ver)), ""]
        L += [f"- {c['id']}: {c['statement']} ({c.get('source')})" for c in ver] + ["", "</details>", ""]
    L += ["## When you're done", "", "```bash", f"cf review done <run-dir> --minutes <n> --corrections <n>", "```", "",
          "Every correction you make that the checker passed becomes an eval case, so the checker learns what it missed.", ""]
    return "\n".join(L)


def check(md: str, run_dir: Path, snap: dict, brief: dict | None = None, use_model: bool = True,
          source: str = "in-house") -> dict:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "draft.md").write_text(md, encoding="utf-8")
    fc = factcheck.run(md, snap, use_model)
    write_json(run_dir / "factcheck.json", fc)
    issues = lint.run(md, (brief or {}).get("format"), lint.blueprint_fields(snap))
    write_json(run_dir / "lint.json", issues)
    est = review_estimate(fc, issues)
    (run_dir / "review-packet.md").write_text(packet(run_dir.parent.name, fc, issues, est, brief), encoding="utf-8")
    reasons = []
    if fc["contradicted"]:
        reasons.append(f"{fc['contradicted']} contradicted claims")
    if any(i["severity"] == "error" for i in issues):
        reasons.append(f"{sum(i['severity'] == 'error' for i in issues)} lint errors")
    if fc["dangling_tags"]:
        reasons.append(f"tags with no ledger entry: {', '.join(fc['dangling_tags'])}")
    if fc["tks"]:
        reasons.append(f"{len(fc['tks'])} open TKs")
    status = "blocked" if reasons else ("needs-review" if fc["counts"]["SIGNAL"] or fc["untracked"] else "ready")
    result = {"run": str(run_dir), "status": status, "blocked_by": reasons, "source": source,
              "claims": len(fc["claims"]), "tks": len(fc["tks"]),
              **{f"tier_{k.lower()}": v for k, v in fc["counts"].items()},
              "contradicted": fc["contradicted"], "untracked": len(fc["untracked"]),
              "lint_errors": sum(i["severity"] == "error" for i in issues),
              "lint_warnings": sum(i["severity"] == "warning" for i in issues),
              "auto_verified_rate": round(fc["auto_verified_rate"], 2), **est,
              "snapshot_id": snap["snapshot_id"], "draft_sha": sha(md), "date": today()}
    write_json(run_dir / "result.json", result)
    append_jsonl(STATE / "checks.jsonl", [result])
    return result


def run(brief_path: Path, use_model: bool = True) -> dict:
    brief = json.loads(brief_path.read_text()) if brief_path.suffix == ".json" else parse_brief_md(brief_path.read_text())
    snap = docs.current()
    run_dir = STATE / "runs" / slugify(brief["title"]) / now_id()
    run_dir.mkdir(parents=True, exist_ok=True)
    write_json(run_dir / "brief.json", brief)
    pack = research(brief, snap)
    write_json(run_dir / "source-pack.json", pack)
    md, cost = draft(brief, pack)
    res = check(md, run_dir, snap, brief, use_model)
    res["draft_cost_usd"] = cost
    write_json(run_dir / "result.json", res)
    return res


def parse_brief_md(text: str) -> dict:
    """Briefs are Markdown for humans with a JSON block for the machine."""
    m = re.search(r"```json\n(.*?)```", text, re.S)
    if not m:
        raise SystemExit("brief has no ```json block")
    return json.loads(m.group(1))


def publish(run_dir: Path, out_dir: Path, force: bool = False) -> Path:
    """Strip the ledger from the page, and record what the page depends on
    in the catalog: every claim, the docs section it cites, and the hash of
    that section when it was checked. The refresh job reads this."""
    res = read_json(run_dir / "result.json")
    if res["status"] == "blocked" and not force:
        raise SystemExit(f"{run_dir} is blocked: {'; '.join(res.get('blocked_by', []))}")
    md = (run_dir / "draft.md").read_text(encoding="utf-8")
    fc = read_json(run_dir / "factcheck.json")
    fm = lint.frontmatter(md)
    slug = slugify(fm.get("title", run_dir.parent.name))
    out_dir.mkdir(parents=True, exist_ok=True)
    page = out_dir / f"{slug}.md"
    clean = re.sub(r"\s*\[C\d+\]", "", factcheck.body_of(md)).rstrip() + "\n"
    page.write_text(clean, encoding="utf-8")
    cat = read_json(STATE / "catalog.json", {"pages": {}})
    cat["pages"][slug] = {
        "path": str(page), "title": fm.get("title"), "format": fm.get("format"),
        "target_questions": re.findall(r"[\w-]+", fm.get("target_questions", "")),
        "published": today(), "last_verified": today(), "run": str(run_dir),
        "snapshot_id": res["snapshot_id"],
        "claims": [{"id": c["id"], "statement": c["statement"], "source": c.get("source"),
                    "source_sha": c.get("evidence_sha"), "tier": c["tier"]} for c in fc["claims"]],
    }
    write_json(STATE / "catalog.json", cat)
    return page
