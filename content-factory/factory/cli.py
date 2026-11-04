"""cf: the content factory command line. Run `cf help` for the commands."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from . import briefs, docs, evals, gaps, metrics, pipeline, refresh, signals, survey
from .common import ROOT, STATE, append_jsonl, read_json, today, write_json


def p_docs(a):
    if a.action == "snapshot":
        is_url = a.src.startswith(("http://", "https://"))
        snap = docs.build(a.src if is_url else Path(a.src))
        readme = Path(a.src) / "README.md"
        snap["fixture"] = bool(a.fixture or (not is_url and readme.exists() and "Synthetic" in readme.read_text()))
        out = docs.save(snap, a.name)
        print(f"{len(snap['sections'])} sections -> {out}{' (fixture)' if snap['fixture'] else ''}")
    elif a.action == "gaps":
        md = docs.gaps_report(STATE, docs.current())
        (STATE / "docs-gaps.md").write_text(md, encoding="utf-8")
        print(md)
    elif a.action == "diff":
        d = docs.diff(read_json(Path(a.old)), read_json(Path(a.new)))
        print(json.dumps(d, indent=2))


def p_survey(a):
    if a.resummarize:
        print((survey.resummarize(Path(a.resummarize), a.rescore) / "summary.md").read_text()); return
    out = survey.run(engine=a.engine, k=a.k, select=a.only, use_judge=not a.no_judge, workers=a.workers,
                     out_dir=Path(a.out).resolve() if a.out else None)
    print((out / "summary.md").read_text())


def latest_survey(path: str | None) -> Path:
    p = Path(path) if path else survey.latest_dir()
    if not p or not (p / "summary.json").exists():
        sys.exit("no survey found: run `cf survey` or pass --survey DIR")
    return p


def p_gaps(a):
    sdir = latest_survey(a.survey)
    s = read_json(sdir / "summary.json")
    traffic = signals.traffic(Path(a.traffic)) if a.traffic else {"by_path": {}}
    cites = signals.citations(Path(a.citations)) if a.citations else []
    cat = read_json(STATE / "catalog.json", {"pages": {}})
    b = gaps.backlog(s, survey.questions(), cat, traffic, cites)
    meta = (f"From survey {s['survey_id']} ({s['answers']} answers, {', '.join(s['engines'])})"
            + (f", agent traffic from {a.traffic}" if a.traffic else "")
            + (f", citations from {a.citations}" if a.citations else "") + ".")
    b["meta"] = meta
    write_json(STATE / "backlog.json", b)
    md = gaps.render_md(b, meta)
    (STATE / "backlog.md").write_text(md, encoding="utf-8")
    print(md)


def p_brief(a):
    b = read_json(STATE / "backlog.json")
    if not b:
        sys.exit("no backlog: run `cf gaps` first")
    item = b["items"][a.n - 1]
    data, md = briefs.make(item, docs.current())
    out = Path(a.out or STATE / "briefs")
    out.mkdir(parents=True, exist_ok=True)
    p = out / f"{data['id']}.md"
    p.write_text(md, encoding="utf-8")
    print(p)


def show(res):
    print(json.dumps({k: res[k] for k in ("status", "blocked_by", "claims", "tks", "tier_verified", "tier_corroborated", "tier_signal",
                                          "contradicted", "untracked", "lint_errors", "estimated_minutes")}, indent=2))
    print(f"review packet: {res['run']}/review-packet.md")


def p_run(a):
    res = pipeline.run(Path(a.brief), use_model=not a.no_model_judge)
    show(res)
    sys.exit(1 if res["status"] == "blocked" else 0)


def p_check(a):
    md = Path(a.draft).read_text(encoding="utf-8")
    brief = pipeline.parse_brief_md(Path(a.brief).read_text()) if a.brief else None
    from .common import now_id, slugify
    run_dir = STATE / "checks" / slugify(Path(a.draft).stem) / now_id()
    res = pipeline.check(md, run_dir, docs.current(), brief, not a.no_model_judge,
                         source=f"partner:{a.partner}" if a.partner else "in-house")
    show(res)
    sys.exit(1 if res["status"] == "blocked" else 0)


def p_publish(a):
    print(pipeline.publish(Path(a.run), Path(a.out or STATE / "published"), a.force))


def p_refresh(a):
    q = refresh.queue(read_json(STATE / "catalog.json", {"pages": {}}), docs.current(), not a.no_model_judge)
    write_json(STATE / "refresh-queue.json", q)
    md = refresh.render_md(q)
    (STATE / "refresh-queue.md").write_text(md, encoding="utf-8")
    print(md)
    sys.exit(1 if any(p["priority"] == "now" for p in q["pages"]) and a.strict else 0)


def p_eval(a):
    use_model = not a.no_model_judge
    cur = evals.run(docs.current(), use_model=use_model)
    allb = read_json(evals.BASELINE, {})
    base = allb.get(evals.mode(use_model))
    reg = evals.compare(cur, base)
    print(evals.render(cur, base, reg))
    if a.save_baseline:
        allb[evals.mode(use_model)] = {k: cur[k] for k in ("factcheck", "lint", "brands")}
        write_json(evals.BASELINE, allb)
        print(f"baseline saved to {evals.BASELINE}")
    sys.exit(1 if reg and not a.save_baseline else 0)


def p_review(a):
    run = Path(a.run)
    row = {"run": str(run), "date": today(), "minutes": a.minutes, "corrections": a.corrections,
           "escaped": len(a.escaped or [])}
    est = read_json(run / "result.json", {})
    row["estimated_minutes"] = est.get("estimated_minutes")
    append_jsonl(STATE / "reviews.jsonl", [row])
    for cid in a.escaped or []:
        # The checker passed it and a human caught it: that's a test case.
        md = (run / "draft.md").read_text(encoding="utf-8")
        case = evals.CASES / f"escaped-{run.parent.name}-{run.name}-{cid}.md"
        fm = f"---\nexpect_flagged: {cid}\nsource: reviewer correction {today()}\n"
        body = md[4:] if md.startswith("---\n") else "---\n" + md
        case.write_text(fm + body, encoding="utf-8")
        print(f"eval case added: {case}")
    print(f"recorded {a.minutes} min review of {run}")


def p_state(a):
    from . import store
    url = a.url or store.url_from_env()
    if not url:
        sys.exit("set CF_STATE_URL (postgresql://... or sqlite:///...) or pass --url")
    r = (store.pull if a.action == "pull" else store.push)(url)
    print(f"{a.action}: {r['files']} files, {r['lines']} log lines")


def p_metrics(a):
    md = metrics.scorecard(a.targets.split(",") if a.targets else None)
    (STATE / "scorecard.md").write_text(md, encoding="utf-8")
    print(md)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="cf", description="Render content factory")
    sp = ap.add_subparsers(dest="cmd")

    d = sp.add_parser("docs", help="snapshot or diff the docs, or list the docs gaps drafts hit")
    d.add_argument("action", choices=["snapshot", "diff", "gaps"])
    d.add_argument("--from", dest="src", help="docs folder, llms-full.txt file, or its URL"); d.add_argument("--name"); d.add_argument("--fixture", action="store_true")
    d.add_argument("old", nargs="?"); d.add_argument("new", nargs="?")
    d.set_defaults(f=p_docs)

    s = sp.add_parser("survey", help="ask answer engines the question set")
    s.add_argument("--engine", default="claude"); s.add_argument("-k", type=int, default=3)
    s.add_argument("--only"); s.add_argument("--no-judge", action="store_true")
    s.add_argument("--workers", type=int, default=6); s.add_argument("--out")
    s.add_argument("--resummarize", metavar="DIR", help="rebuild a saved survey's summary without new calls")
    s.add_argument("--rescore", action="store_true", help="with --resummarize: rerun mention detection on saved answers")
    s.set_defaults(f=p_survey)

    g = sp.add_parser("gaps", help="diagnose gaps and rank the backlog")
    g.add_argument("--survey"); g.add_argument("--traffic"); g.add_argument("--citations")
    g.set_defaults(f=p_gaps)

    b = sp.add_parser("brief", help="write a brief for backlog item N")
    b.add_argument("n", type=int); b.add_argument("--out"); b.set_defaults(f=p_brief)

    r = sp.add_parser("run", help="research, draft, check a brief")
    r.add_argument("brief"); r.add_argument("--no-model-judge", action="store_true"); r.set_defaults(f=p_run)

    c = sp.add_parser("check", help="fact-check and lint a draft (in-house or partner)")
    c.add_argument("draft"); c.add_argument("--brief"); c.add_argument("--partner")
    c.add_argument("--no-model-judge", action="store_true"); c.set_defaults(f=p_check)

    pu = sp.add_parser("publish", help="publish a checked run and record its claims")
    pu.add_argument("run"); pu.add_argument("--out"); pu.add_argument("--force", action="store_true")
    pu.set_defaults(f=p_publish)

    rf = sp.add_parser("refresh", help="flag published claims whose docs changed")
    rf.add_argument("--no-model-judge", action="store_true"); rf.add_argument("--strict", action="store_true")
    rf.set_defaults(f=p_refresh)

    e = sp.add_parser("eval", help="score the checker against planted errors")
    e.add_argument("--save-baseline", action="store_true"); e.add_argument("--no-model-judge", action="store_true")
    e.set_defaults(f=p_eval)

    rv = sp.add_parser("review", help="record an expert review")
    rv.add_argument("action", choices=["done"]); rv.add_argument("run")
    rv.add_argument("--minutes", type=float, required=True); rv.add_argument("--corrections", type=int, default=0)
    rv.add_argument("--escaped", nargs="*", help="claim IDs the reviewer fixed that the checker passed")
    rv.set_defaults(f=p_review)

    st = sp.add_parser("state", help="sync CF_STATE with a database (for runs on fresh compute)")
    st.add_argument("action", choices=["pull", "push"]); st.add_argument("--url")
    st.set_defaults(f=p_state)

    m = sp.add_parser("metrics", help="print the scorecard"); m.add_argument("--targets"); m.set_defaults(f=p_metrics)

    a = ap.parse_args(argv)
    if not getattr(a, "f", None):
        ap.print_help(); return
    a.f(a)


if __name__ == "__main__":
    main()
