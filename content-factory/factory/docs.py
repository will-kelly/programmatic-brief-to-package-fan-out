"""Docs snapshots. A snapshot splits every docs page into sections and
hashes each one, so the fact-checker has evidence to quote and the refresh
job can tell exactly which section changed between two snapshots.

Section IDs look like `free#spin-down`: page stem, then the heading anchor
(an explicit `{#anchor}` or the slugified heading text).

Sources:
  a directory of Markdown files (a clone of the docs repo, or the fixture)
  an llms-full.txt style file, split on `# ` page headings with `Source:` URLs
"""

from __future__ import annotations

import re
from pathlib import Path

from .common import STATE, now_id, read_json, sha, slugify, write_json

HEAD_RE = re.compile(r"^(#{2,3})\s+(.*?)\s*(?:\{#([\w-]+)\})?\s*$")


def split_page(stem: str, text: str) -> dict[str, dict]:
    sections: dict[str, dict] = {}
    title = next((l[2:].strip() for l in text.splitlines() if l.startswith("# ")), stem)
    cur_id, cur_head, buf = f"{stem}#intro", title, []

    def flush():
        body = "\n".join(buf).strip()
        if body:
            sections[cur_id] = {"page": stem, "heading": cur_head, "text": body, "sha": sha(body)}

    for line in text.splitlines():
        m = HEAD_RE.match(line)
        if m:
            flush()
            cur_head = m.group(2)
            cur_id = f"{stem}#{m.group(3) or slugify(cur_head)}"
            buf = []
        elif not line.startswith("# "):
            buf.append(line)
    flush()
    return sections


def fetch(url: str, dest: Path) -> Path:
    """Download an llms-full.txt (or any Markdown dump) to snapshot from."""
    import urllib.request
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "content-factory-docs-snapshot"})
    with urllib.request.urlopen(req, timeout=60) as r:
        dest.write_bytes(r.read())
    return dest


def build(src: Path) -> dict:
    sections: dict[str, dict] = {}
    if str(src).startswith(("http://", "https://")):
        src = fetch(str(src), STATE / "docs" / "source" / (slugify(str(src)) + ".txt"))
    if src.is_dir():
        for f in sorted(src.glob("**/*.md")):
            if f.name.lower() == "readme.md":
                continue
            stem = str(f.relative_to(src).with_suffix("")).replace("/", "-")
            sections.update(split_page(stem, f.read_text(encoding="utf-8")))
    else:
        text = src.read_text(encoding="utf-8")
        for chunk in re.split(r"(?m)^(?=# )", text):
            if not chunk.strip():
                continue
            m = re.search(r"(?m)^Source:\s*(\S+)", chunk)
            stem = slugify(m.group(1).rstrip("/").rsplit("/", 1)[-1]) if m else slugify(chunk.splitlines()[0])
            sections.update(split_page(stem, chunk))
    return {"source": str(src), "snapshot_id": now_id(), "sections": sections}


def save(snap: dict, name: str | None = None) -> Path:
    p = STATE / "docs" / f"{name or snap['snapshot_id']}.json"
    write_json(p, snap)
    write_json(STATE / "docs" / "current.json", snap)
    return p


def current() -> dict:
    snap = read_json(STATE / "docs" / "current.json")
    if snap is None:
        raise SystemExit("no docs snapshot yet: run `cf docs snapshot --from <dir>` first")
    return snap


def diff(old: dict, new: dict) -> dict:
    o, n = old["sections"], new["sections"]
    return {
        "changed": sorted(k for k in o.keys() & n.keys() if o[k]["sha"] != n[k]["sha"]),
        "removed": sorted(o.keys() - n.keys()),
        "added": sorted(n.keys() - o.keys()),
    }


WORD = re.compile(r"[a-z0-9][a-z0-9.+-]{2,}")
STOP = set("the and for with that this you your are can how what where when which should does from into have has not use using than then them they will about only out app".split())


def terms(text: str) -> list[str]:
    return [w for w in WORD.findall(text.lower()) if w not in STOP]


def search(snap: dict, query: str, k: int = 8) -> list[tuple[str, float]]:
    """Plain term-overlap ranking. Good enough to build a source pack; the
    drafting model gets the top sections and nothing else."""
    import math
    secs = snap["sections"]
    df: dict[str, int] = {}
    toks = {sid: set(terms(s["heading"] + " " + s["text"])) for sid, s in secs.items()}
    for t in toks.values():
        for w in t:
            df[w] = df.get(w, 0) + 1
    q = set(terms(query))
    n = len(secs)
    scored = []
    for sid, t in toks.items():
        sc = sum(math.log(1 + n / df[w]) for w in q & t)
        if sc:
            scored.append((sid, round(sc, 2)))
    return sorted(scored, key=lambda kv: -kv[1])[:k]


def gaps_report(state_dir: Path, snap: dict | None = None) -> str:
    """Every [[TK]] left in a draft is a question the content needed and the
    docs couldn't answer. Grouped, they're a work list for the docs owners,
    ranked by how many pieces got stuck on the same missing fact."""
    from collections import defaultdict
    hits = defaultdict(set)
    packs: dict[str, set] = defaultdict(set)
    latest: dict[str, Path] = {}
    for d in sorted(state_dir.glob("runs/*/*/factcheck.json")):
        latest[d.parent.parent.name] = d          # run IDs sort by time
    for d in latest.values():
        fc = read_json(d)
        pack = {s["id"] for s in read_json(d.parent / "source-pack.json", {"sections": []})["sections"]}
        for t in fc.get("tks", []):
            key = re.sub(r"\s+", " ", t.strip().rstrip(".")).lower()
            hits[key].add(d.parent.parent.name)
            packs[key] |= pack
    L = ["# Docs gaps from drafts", "",
         f"{len(hits)} distinct facts the drafts needed and the docs snapshot didn't state. "
         "Close one in the docs and every page waiting on it can be finished, and answer engines get the fact from the source.", "",
         "A section in the last column means the snapshot may answer it but the research stage left that section out of the source pack. "
         "That's a retrieval miss to fix in the factory, not a docs gap. Confirm before filing it with the docs team.", "",
         "| Missing fact | Pieces blocked | Possibly answered by |", "|---|---|---|"]
    for t, pieces in sorted(hits.items(), key=lambda kv: -len(kv[1])):
        maybe = ""
        if snap:
            top = search(snap, t, k=1)
            # Strong overlap only; weak matches are noise.
            if top and top[0][1] >= 6 and top[0][0] not in packs[t]:
                maybe = f"`{top[0][0]}`"
        L.append(f"| {t} | {len(pieces)} | {maybe} |")
    return "\n".join(L) + "\n"
