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
  3. the decorator's retry argument name (`retry` below is a placeholder)
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from render_sdk import Workflows  # VERIFY: import path for your SDK version

from factory import docs, gaps, pipeline, refresh, signals, survey
from factory.common import STATE, read_json, read_jsonl, write_json

app = Workflows()

# State lives on a mounted disk or object storage in production; the
# factory reads CF_STATE, so point it there.
DOCS_SRC = Path(os.environ.get("CF_DOCS_SRC", "/var/data/docs"))


@app.task(timeout_seconds=600)
async def snapshot_docs() -> str:
    snap = docs.build(DOCS_SRC)
    return str(docs.save(snap))


@app.task(timeout_seconds=1800)
async def survey_cluster(cluster: str, k: int = 3) -> str:
    # One task per cluster, so a slow or rate-limited engine fails one
    # cluster and the retry covers only that cluster.
    return str(survey.run(engine="claude", k=k, select=cluster,
                          out_dir=STATE / "surveys" / f"pending-{cluster}"))


@app.task(timeout_seconds=900)
async def refresh_queue() -> dict:
    q = refresh.queue(read_json(STATE / "catalog.json", {"pages": {}}), docs.current())
    write_json(STATE / "refresh-queue.json", q)
    return {"pages": len(q["pages"]), "broken": sum(p["broken"] for p in q["pages"])}


@app.task(timeout_seconds=600)
async def gap_analysis(survey_dirs: list[str]) -> dict:
    rows = []
    for d in survey_dirs:
        rows += read_jsonl(Path(d) / "answers.jsonl")
    s = survey.summarize(rows, survey.questions())
    traffic_log = os.environ.get("CF_TRAFFIC_LOG")
    traffic = signals.traffic(Path(traffic_log)) if traffic_log else {"by_path": {}}
    b = gaps.backlog(s, survey.questions(), read_json(STATE / "catalog.json", {"pages": {}}), traffic, [])
    write_json(STATE / "backlog.json", b)
    return {"items": len(b["items"]), "counts": b["counts"]}


@app.task(timeout_seconds=7200)
async def weekly_cycle() -> dict:
    await snapshot_docs()
    clusters = sorted({q["cluster"] for q in survey.questions()})
    dirs = await asyncio.gather(*(survey_cluster(c) for c in clusters))
    fresh = await refresh_queue()
    backlog = await gap_analysis(list(dirs))
    return {"refresh": fresh, "backlog": backlog}


@app.task(timeout_seconds=1200)
async def produce(brief_path: str) -> dict:
    # Ends at the review packet on purpose. Publishing waits for a human.
    return pipeline.run(Path(brief_path))


if __name__ == "__main__":
    app.start()
