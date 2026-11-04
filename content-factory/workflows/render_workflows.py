"""Run the factory on Render Workflows.

The factory's stages are plain functions over files (factory/pipeline.py),
so this module only maps them onto tasks. Nothing in factory/ imports the
SDK, which keeps every stage runnable and testable on a laptop.

Task graph:

    weekly_cycle
      ├─ snapshot_docs                     docs -> section hashes
      ├─ survey (fan-out by cluster)       questions -> scored answers
      ├─ refresh_queue                     catalog x new snapshot -> flagged claims
      └─ gap_analysis                      survey + signals -> backlog
    produce(brief)                         one piece, on demand or per backlog item
      ├─ research -> draft -> check        retried per stage, not per piece
      └─ (human review, then `cf publish`)

VERIFY BEFORE DEPLOYING. This was written against the documented pattern
(a `Workflows` app object, `@app.task(...)` with `timeout_seconds`, and
`app.start()` in the entry point) without access to the live SDK
reference. Check three things against render.com/docs/workflows-sdk-python
for the SDK version you pin:
  1. the import path for `Workflows`
  2. whether tasks call each other with `await task(...)` as below
  3. whether a task can return a dict, or needs a JSON string
"""

from __future__ import annotations

import asyncio
import functools
import os
from pathlib import Path

from render_sdk import Workflows  # VERIFY: import path for your SDK version

from factory import docs, gaps, pipeline, refresh, signals, store, survey
from factory.common import STATE, now_id, read_json, write_json

app = Workflows()

# Production settings, set as environment variables on the service:
#   CF_LLM=anthropic            Messages API, not the claude CLI
#   ANTHROPIC_API_KEY           secret
#   CF_STATE_URL                Render Postgres internal connection string
#   CF_DOCS_SRC                 docs URL (llms-full.txt) or a path
#   CF_TRAFFIC_LOG              optional: path or URL of an agent access log
DOCS_SRC = os.environ.get("CF_DOCS_SRC", "https://render.com/docs/llms-full.txt")


def synced(fn):
    """Each task may start on fresh compute, so it pulls state from the
    database first and pushes what it changed when it's done, even on
    failure, so a crashed task's logs and partial survey rows aren't lost.
    Append-only logs merge row by row, so parallel tasks don't clobber
    each other (see factory/store.py)."""
    @functools.wraps(fn)
    async def run(*args, **kwargs):
        url = store.url_from_env()
        if url:
            store.pull(url)
        try:
            return await fn(*args, **kwargs)
        finally:
            if url:
                store.push(url)
    return run


@app.task(timeout_seconds=600)
@synced
async def snapshot_docs() -> str:
    snap = docs.build(DOCS_SRC if DOCS_SRC.startswith("http") else Path(DOCS_SRC))
    snap["fixture"] = False
    return str(docs.save(snap))


@app.task(timeout_seconds=1800)
@synced
async def survey_cluster(run_id: str, cluster: str, k: int = 3) -> str:
    # One task per cluster: a rate-limited or failing engine fails one
    # cluster, and the retry reruns only that cluster.
    out = STATE / "surveys" / f"{run_id}-parts" / cluster
    survey.run(engine="claude", k=k, select=cluster, out_dir=out)
    return str(out.relative_to(STATE))


@app.task(timeout_seconds=900)
@synced
async def refresh_queue() -> dict:
    q = refresh.queue(read_json(STATE / "catalog.json", {"pages": {}}), docs.current())
    write_json(STATE / "refresh-queue.json", q)
    (STATE / "refresh-queue.md").write_text(refresh.render_md(q), encoding="utf-8")
    return {"pages": len(q["pages"]), "broken": sum(p["broken"] for p in q["pages"])}


@app.task(timeout_seconds=600)
@synced
async def gap_analysis(run_id: str, parts: list[str]) -> dict:
    merged = survey.merge([STATE / p for p in parts], STATE / "surveys" / run_id)
    s = read_json(merged / "summary.json")
    log = os.environ.get("CF_TRAFFIC_LOG")
    traffic = signals.traffic(Path(log)) if log else {"by_path": {}}
    b = gaps.backlog(s, survey.questions(), read_json(STATE / "catalog.json", {"pages": {}}), traffic, [])
    meta = f"From survey {run_id} ({s['answers']} answers)."
    b["meta"] = meta
    write_json(STATE / "backlog.json", b)
    (STATE / "backlog.md").write_text(gaps.render_md(b, meta), encoding="utf-8")
    return {"items": len(b["items"]), "counts": b["counts"]}


@app.task(timeout_seconds=7200)
async def weekly_cycle(k: int = 3) -> dict:
    # Not @synced itself: it only coordinates, and each child task syncs.
    # VERIFY: that awaiting a task from a task runs it as a subtask.
    run_id = now_id()
    await snapshot_docs()
    clusters = sorted({q["cluster"] for q in survey.questions()})
    parts = await asyncio.gather(*(survey_cluster(run_id, c, k) for c in clusters))
    fresh = await refresh_queue()
    backlog = await gap_analysis(run_id, list(parts))
    return {"run_id": run_id, "refresh": fresh, "backlog": backlog}


@app.task(timeout_seconds=1200)
@synced
async def produce(brief_path: str) -> dict:
    # Ends at the review packet on purpose. Publishing waits for a person.
    p = Path(brief_path)
    return pipeline.run(p if p.is_absolute() else STATE / p)


if __name__ == "__main__":
    app.start()
