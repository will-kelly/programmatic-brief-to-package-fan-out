"""The recurring LLM answer survey.

Ask every question in config/questions.toml `k` times per engine, then read
each answer for: is Render mentioned, where it ranks among the platforms
named, who gets recommended first, which URLs get cited, and whether what
the answer says about Render is true.

One answer is an anecdote. Answers are sampled, so the survey reports a
mention *rate* per question with a Wilson interval, and the gap analysis
only acts on differences the interval can support.

Engines:
  claude          asked live through factory.llm (no web search: this is the
                  model's own knowledge, the thing training-crawler traffic
                  feeds)
  import:FILE     answers collected elsewhere (Perplexity, ChatGPT search,
                  Google AI Overviews, or a vendor tracker export) as JSONL
                  rows: {question_id, engine, answer, cited_urls?}
"""

from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import llm
from .brands import Brands
from .common import (STATE, append_jsonl, extract_json, load_toml, now_id, pct,
                     read_jsonl, today, wilson, write_json)

JUDGE_SYSTEM = """You audit what an AI assistant's answer says about the cloud platform Render (render.com).
You get the answer and a registry of known facts. List every factual claim the answer makes about Render specifically: features, limits, pricing, behavior, what it can or can't run. Skip opinions ("easiest", "great DX") and claims about other platforms.
For each claim return:
  claim: the claim, quoted or tightly paraphrased
  verdict: "consistent" (agrees with a registry fact), "contradicts" (conflicts with a registry fact), or "uncovered" (the registry doesn't address it)
  fact_id: the registry fact ID it agrees or conflicts with, or null
Reply with a JSON array only. An answer with no Render claims gets []."""


def questions(select: str | None = None) -> list[dict]:
    qs = load_toml("questions.toml")["question"]
    if select:
        keep = set(select.split(","))
        qs = [q for q in qs if q["id"] in keep or q["cluster"] in keep]
    return qs


def facts() -> list[dict]:
    return load_toml("facts.toml")["fact"]


def pattern_hits(answer: str, fs: list[dict]) -> list[dict]:
    """Known-wrong statements caught without a model."""
    hits = []
    for f in fs:
        for p in f.get("wrong_patterns", []):
            m = re.search(p, answer, re.I)
            if m:
                hits.append({"claim": m.group(0), "verdict": "contradicts",
                             "fact_id": f["id"], "by": "pattern"})
    return hits


def judge(answer: str, fs: list[dict]) -> list[dict]:
    registry = "\n".join(f"{f['id']}: {f['statement']}" for f in fs)
    r = llm.ask(f"REGISTRY\n{registry}\n\nANSWER\n{answer}", JUDGE_SYSTEM, role="survey-judge")
    try:
        out = extract_json(r.text)
    except ValueError:
        return [{"claim": "(judge reply unreadable)", "verdict": "uncovered", "fact_id": None, "by": "model"}]
    return [dict(c, by="model") for c in out if isinstance(c, dict)]


def score(row: dict, brands: Brands, fs: list[dict], use_judge: bool) -> dict:
    a = row["answer"]
    ms = brands.mentions(a)
    us = next((m for m in ms if m["brand"] == brands.us), None)
    cites = brands.citations(a, row.get("cited_urls", []))
    claims = []
    if us:
        claims = pattern_hits(a, fs)
        if use_judge:
            claims += judge(a, fs)
        # One verdict per fact per answer; the pattern hit wins a tie.
        seen, deduped = set(), []
        for c in claims:
            key = (c.get("fact_id"), c["verdict"]) if c.get("fact_id") else (c["claim"], c["verdict"])
            if key not in seen:
                seen.add(key); deduped.append(c)
        claims = deduped
    return {
        **row,
        "mentions": [m["brand"] for m in ms],
        "us_mentioned": bool(us),
        "us_rank": us["rank"] if us else None,
        "brands_named": len(ms),
        "first_pick": brands.first_recommendation(a),
        "citations": cites,
        "us_cited": any(c["owner"] == brands.us for c in cites),
        "render_claims": claims,
        "wrong": sum(1 for c in claims if c["verdict"] == "contradicts"),
    }


def run(engine: str = "claude", k: int = 3, select: str | None = None,
        use_judge: bool = True, workers: int = 6, out_dir: Path | None = None) -> Path:
    brands, fs = Brands(), facts()
    sid = now_id()
    out_dir = out_dir or STATE / "surveys" / sid
    out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []

    if engine.startswith("import:"):
        src = Path(engine.split(":", 1)[1])
        rows = [dict(r, sample=r.get("sample", i)) for i, r in enumerate(read_jsonl(src))]
    else:
        jobs = [(q, s) for q in questions(select) for s in range(k)]

        def one(job):
            q, s = job
            r = llm.ask(q["text"], "You are a helpful assistant.", role="survey-answer")
            return {"question_id": q["id"], "engine": engine, "sample": s,
                    "answer": r.text, "cost_usd": r.cost_usd, "model": r.model}

        with ThreadPoolExecutor(workers) as ex:
            rows = list(ex.map(one, jobs))

    with ThreadPoolExecutor(workers) as ex:
        scored = list(ex.map(lambda r: score(r, brands, fs, use_judge), rows))

    append_jsonl(out_dir / "answers.jsonl", scored)
    summary = summarize(scored, questions())
    summary.update({"survey_id": sid, "date": today(), "engines": sorted({r["engine"] for r in scored}),
                    "samples_per_question": k})
    write_json(out_dir / "summary.json", summary)
    (out_dir / "summary.md").write_text(render_md(summary), encoding="utf-8")
    (STATE / "surveys").mkdir(parents=True, exist_ok=True)
    set_latest(out_dir)
    return out_dir


def set_latest(out_dir: Path) -> None:
    """Point LATEST at a survey. Relative to CF_STATE when the survey lives
    there, so the pointer survives a state pull onto another machine."""
    (STATE / "surveys").mkdir(parents=True, exist_ok=True)
    d = out_dir.resolve()
    try:
        ref = d.relative_to(STATE.resolve()).as_posix()
    except ValueError:
        ref = str(d)
    (STATE / "surveys" / "LATEST").write_text(ref + "\n")


def resummarize(out_dir: Path, rescore: bool = False) -> Path:
    """Rebuild summary files from saved answers, no new answer calls.
    --rescore reruns mention detection (and the judge, if asked) on the
    saved answer text, which is how a brand-detection fix gets applied to
    old surveys."""
    rows = read_jsonl(out_dir / "answers.jsonl")
    old = json.loads((out_dir / "summary.json").read_text()) if (out_dir / "summary.json").exists() else {}
    if rescore:
        brands, fs = Brands(), facts()
        keep = ("question_id", "engine", "sample", "answer", "cost_usd", "model", "cited_urls")
        rows = [score({k: r[k] for k in keep if k in r} | {"render_claims_prev": r.get("render_claims", [])}, brands, fs, False) for r in rows]
        for r in rows:
            prev = [c for c in r.pop("render_claims_prev") if c.get("by") == "model"]
            r["render_claims"] += [c for c in prev if (c.get("fact_id"), c["verdict"]) not in {(x.get("fact_id"), x["verdict"]) for x in r["render_claims"]}]
            r["wrong"] = sum(1 for c in r["render_claims"] if c["verdict"] == "contradicts")
        (out_dir / "answers.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    summary = summarize(rows, questions())
    summary.update({"survey_id": old.get("survey_id", out_dir.name), "date": old.get("date", today()),
                    "engines": sorted({r["engine"] for r in rows}),
                    "samples_per_question": max(r["sample"] for r in rows) + 1})
    write_json(out_dir / "summary.json", summary)
    (out_dir / "summary.md").write_text(render_md(summary), encoding="utf-8")
    return out_dir


def latest_dir() -> Path | None:
    p = STATE / "surveys" / "LATEST"
    if not p.exists():
        return None
    ref = Path(p.read_text().strip())
    return ref if ref.is_absolute() else STATE / ref


def is_branded(q: dict, brands: Brands | None = None) -> bool:
    """A question that names Render always gets Render back. Score it for
    accuracy only, never for visibility."""
    brands = brands or Brands()
    return any(m["brand"] == brands.us for m in brands.mentions(q.get("text", "")))


def merge(dirs: list[Path], out_dir: Path) -> Path:
    """Combine per-cluster survey runs (one Workflows task each) into one
    survey, then summarize it as if it had run in one go."""
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = [r for d in dirs for r in read_jsonl(Path(d) / "answers.jsonl")]
    (out_dir / "answers.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    k = max((r["sample"] for r in rows), default=0) + 1
    summary = summarize(rows, questions())
    summary.update({"survey_id": out_dir.name, "date": today(), "samples_per_question": k,
                    "engines": sorted({r["engine"] for r in rows})})
    write_json(out_dir / "summary.json", summary)
    (out_dir / "summary.md").write_text(render_md(summary), encoding="utf-8")
    set_latest(out_dir)
    return out_dir


def summarize(rows: list[dict], qs: list[dict]) -> dict:
    qmeta = {q["id"]: q for q in qs}
    brands = Brands()
    by_q: dict[str, list[dict]] = {}
    for r in rows:
        by_q.setdefault(r["question_id"], []).append(r)
    per_q = []
    for qid, rs in by_q.items():
        n = len(rs)
        k = sum(r["us_mentioned"] for r in rs)
        lo, hi = wilson(k, n)
        comp: dict[str, int] = {}
        for r in rs:
            for b in r["mentions"]:
                if b != "Render":
                    comp[b] = comp.get(b, 0) + 1
        ranks = [r["us_rank"] for r in rs if r["us_rank"]]
        wrong = [c for r in rs for c in r["render_claims"] if c["verdict"] == "contradicts"]
        cite_owners: dict[str, int] = {}
        for r in rs:
            for c in r["citations"]:
                cite_owners[c["owner"]] = cite_owners.get(c["owner"], 0) + 1
        per_q.append({
            "question_id": qid, "cluster": qmeta.get(qid, {}).get("cluster", "?"),
            "text": qmeta.get(qid, {}).get("text", ""), "n": n,
            "branded": is_branded(qmeta.get(qid, {}), brands),
            "mention_rate": k / n, "ci": [round(lo, 2), round(hi, 2)],
            "first_pick_rate": sum(r["first_pick"] == "Render" for r in rs) / n,
            "avg_rank": round(sum(ranks) / len(ranks), 2) if ranks else None,
            "avg_brands_named": round(sum(r["brands_named"] for r in rs) / n, 1),
            "top_competitors": sorted(comp.items(), key=lambda kv: -kv[1])[:4],
            "wrong_claims": wrong,
            "uncovered_claims": [c for r in rs for c in r["render_claims"] if c["verdict"] == "uncovered"],
            "citation_owners": cite_owners,
        })
    per_q.sort(key=lambda d: (d["cluster"], d["question_id"]))
    clusters: dict[str, dict] = {}
    for q in per_q:
        c = clusters.setdefault(q["cluster"], {"n": 0, "k": 0, "first": 0, "wrong": 0, "branded_n": 0})
        c["wrong"] += len(q["wrong_claims"])
        if q["branded"]:
            c["branded_n"] += q["n"]
            continue
        c["n"] += q["n"]; c["k"] += round(q["mention_rate"] * q["n"])
        c["first"] += round(q["first_pick_rate"] * q["n"])
    for c in clusters.values():
        c["mention_rate"] = c["k"] / c["n"] if c["n"] else None
        c["ci"] = [round(x, 2) for x in wilson(c["k"], c["n"])]
        c["first_pick_rate"] = c["first"] / c["n"] if c["n"] else None
    allc = [c for r in rows for c in r["render_claims"]]
    verdicts = {v: sum(c["verdict"] == v for c in allc) for v in ("consistent", "contradicts", "uncovered")}
    n_all = len(rows)
    branded_ids = {q["question_id"] for q in per_q if q["branded"]}
    open_rows = [r for r in rows if r["question_id"] not in branded_ids]
    no = max(len(open_rows), 1)
    return {
        "answers": n_all, "unbranded_answers": len(open_rows),
        "mention_rate": sum(r["us_mentioned"] for r in open_rows) / no,
        "mention_ci": [round(x, 2) for x in wilson(sum(r["us_mentioned"] for r in open_rows), len(open_rows))],
        "first_pick_rate": sum(r["first_pick"] == "Render" for r in open_rows) / no,
        "answers_with_wrong_claims": sum(1 for r in rows if r["wrong"]),
        "answers_with_pattern_wrong": sum(1 for r in rows if any(c["verdict"] == "contradicts" and c.get("by") == "pattern" for c in r["render_claims"])),
        "claim_verdicts": verdicts,
        # Share of Render claims the registry could rule on at all. Below
        # ~80%, "the model is accurate about Render" isn't a claim the
        # survey can make yet; grow the registry first.
        "registry_coverage": round((verdicts["consistent"] + verdicts["contradicts"]) / max(len(allc), 1), 3),
        "cost_usd": round(sum(r.get("cost_usd", 0) for r in rows), 2),
        "clusters": clusters, "questions": per_q,
    }


def render_md(s: dict) -> str:
    L = [f"# LLM answer survey, {s['date']}", "",
         f"{s['answers']} answers from {', '.join(s['engines'])}, {s['samples_per_question']} samples per question. "
         f"On the {s['unbranded_answers']} answers to questions that don't name Render, Render was mentioned in {pct(s['mention_rate'])} "
         f"(95% CI {pct(s['mention_ci'][0])}–{pct(s['mention_ci'][1])}) and picked first in {pct(s['first_pick_rate'])}. "
         f"{s['answers_with_wrong_claims']} answers were flagged as wrong about Render, "
         f"{s.get('answers_with_pattern_wrong', 0)} of them by a known-wrong pattern.", "",
         f"The fact registry could rule on {pct(s.get('registry_coverage', 0))} of the {sum(s.get('claim_verdicts', {}).values())} Render claims in these answers "
         f"({s.get('claim_verdicts', {}).get('consistent', 0)} consistent, {s.get('claim_verdicts', {}).get('contradicts', 0)} conflicting, "
         f"{s.get('claim_verdicts', {}).get('uncovered', 0)} not covered). Accuracy numbers mean little until that's above 80%.", "",
         "## By cluster", "", "Branded questions (ones that name Render) count toward wrong claims only.", "",
         "| Cluster | Unbranded answers | Mentioned | 95% CI | Picked first | Wrong claims |",
         "|---|---|---|---|---|---|"]
    for name, c in sorted(s["clusters"].items(), key=lambda kv: (kv[1]["mention_rate"] is None, kv[1]["mention_rate"] or 0)):
        if c["mention_rate"] is None:
            L.append(f"| {name} | 0 ({c['branded_n']} branded) | — | — | — | {c['wrong']} |")
        else:
            L.append(f"| {name} | {c['n']} | {pct(c['mention_rate'])} | {pct(c['ci'][0])}–{pct(c['ci'][1])} | {pct(c['first_pick_rate'])} | {c['wrong']} |")
    L += ["", "## By question", "", "| Question | Mentioned | Picked first | Avg rank | Named instead |", "|---|---|---|---|---|"]
    for q in sorted(s["questions"], key=lambda d: (d["branded"], d["mention_rate"])):
        comp = ", ".join(f"{b} ({n})" for b, n in q["top_competitors"])
        tag = " *(branded)*" if q["branded"] else ""
        L.append(f"| `{q['question_id']}` {q['text']}{tag} | {pct(q['mention_rate'])} | {pct(q['first_pick_rate'])} | {q['avg_rank'] or '—'} | {comp} |")
    wrong = [(q["question_id"], c) for q in s["questions"] for c in q["wrong_claims"]]
    if wrong:
        L += ["", "## Wrong about Render", "", "Each row is a claim an answer made that conflicts with the fact registry. Model-judged rows need a human look before they drive work.", "",
              "| Question | Claim | Conflicts with | Caught by |", "|---|---|---|---|"]
        for qid, c in wrong:
            L.append(f"| `{qid}` | {c['claim'][:160].replace('|', '/')} | {c.get('fact_id') or '—'} | {c.get('by', '?')} |")
    return "\n".join(L) + "\n"
