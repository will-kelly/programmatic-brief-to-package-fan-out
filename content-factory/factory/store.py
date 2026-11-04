"""Durable state for runs that don't share a disk.

Locally, the factory's state is a folder (CF_STATE, default ./state). On
Render Workflows each task can run on fresh compute, so a task pulls the
state folder from a database when it starts and pushes its changes back
when it ends:

    cf state pull      database -> CF_STATE
    cf state push      CF_STATE -> database

Two kinds of file, two rules:

  *.jsonl   append-only logs (llm calls, checks, reviews, survey answers).
            Pushed as new rows only, so two tasks appending in parallel
            both keep their rows. If a log was rewritten rather than
            appended to (a survey rescore does this), push replaces it.
  others    whole files (catalog, backlog, snapshots, drafts). Pushed when
            their hash changed since the pull; last writer wins, which is
            fine because only one task type writes each of them.

CF_STATE_URL picks the database:
    postgresql://user:pass@host/db   Render Postgres (needs psycopg)
    sqlite:///path/to/state.db       local, and the tests
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from pathlib import Path

from . import common

MANIFEST = ".store-manifest.json"
SKIP = {MANIFEST, ".lock"}


class DB:
    def __init__(self, url: str):
        self.url = url
        if url.startswith("sqlite:///"):
            self.conn = sqlite3.connect(url[len("sqlite:///"):])
            self.ph = "?"
            blob = "BLOB"
            serial = "INTEGER PRIMARY KEY AUTOINCREMENT"
        elif url.startswith(("postgres://", "postgresql://")):
            import psycopg  # only needed for Postgres
            self.conn = psycopg.connect(url)
            self.ph = "%s"
            blob = "BYTEA"
            serial = "BIGSERIAL PRIMARY KEY"
        else:
            raise SystemExit(f"CF_STATE_URL must start with postgresql:// or sqlite:/// (got {url[:20]}...)")
        cur = self.conn.cursor()
        cur.execute(f"CREATE TABLE IF NOT EXISTS cf_files (path TEXT PRIMARY KEY, sha TEXT NOT NULL, body {blob} NOT NULL)")
        cur.execute(f"CREATE TABLE IF NOT EXISTS cf_lines (id {serial}, path TEXT NOT NULL, line TEXT NOT NULL)")
        cur.execute("CREATE INDEX IF NOT EXISTS cf_lines_path ON cf_lines (path, id)")
        self.conn.commit()

    def q(self, sql: str, args=()):
        cur = self.conn.cursor()
        cur.execute(sql.replace("?", self.ph), args)
        return cur


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _files(root: Path):
    for p in sorted(root.rglob("*")):
        if p.is_file() and not p.is_symlink() and p.name not in SKIP:
            yield p.relative_to(root).as_posix(), p


def pull(url: str, root: Path | None = None) -> dict:
    root = Path(root or common.STATE)
    db = DB(url)
    root.mkdir(parents=True, exist_ok=True)
    manifest = {"files": {}, "lines": {}}
    n_files = n_lines = 0
    for path, sha, body in db.q("SELECT path, sha, body FROM cf_files").fetchall():
        dest = root / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(bytes(body))
        manifest["files"][path] = sha
        n_files += 1
    rows = db.q("SELECT path, line FROM cf_lines ORDER BY id").fetchall()
    by_path: dict[str, list[str]] = {}
    for path, line in rows:
        by_path.setdefault(path, []).append(line)
    for path, lines in by_path.items():
        dest = root / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("".join(l + "\n" for l in lines), encoding="utf-8")
        manifest["lines"][path] = {"n": len(lines), "sha": _sha("\n".join(lines).encode())}
        n_lines += len(lines)
    (root / MANIFEST).write_text(json.dumps(manifest), encoding="utf-8")
    db.conn.close()
    return {"files": n_files, "lines": n_lines}


def push(url: str, root: Path | None = None) -> dict:
    root = Path(root or common.STATE)
    db = DB(url)
    mp = root / MANIFEST
    manifest = json.loads(mp.read_text()) if mp.exists() else {"files": {}, "lines": {}}
    n_files = n_lines = 0
    for path, p in _files(root):
        if path.endswith(".jsonl"):
            lines = [l for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
            prev = manifest["lines"].get(path, {"n": 0, "sha": _sha(b"")})
            seen = prev["n"]
            if len(lines) < seen or _sha("\n".join(lines[:seen]).encode()) != prev["sha"]:
                # Rewritten, not appended: replace what the database holds.
                db.q("DELETE FROM cf_lines WHERE path = ?", (path,))
                seen = 0
            new = lines[seen:]
            for l in new:
                db.q("INSERT INTO cf_lines (path, line) VALUES (?, ?)", (path, l))
            manifest["lines"][path] = {"n": len(lines), "sha": _sha("\n".join(lines).encode())}
            n_lines += len(new)
        else:
            body = p.read_bytes()
            sha = _sha(body)
            if manifest["files"].get(path) == sha:
                continue
            db.q("DELETE FROM cf_files WHERE path = ?", (path,))
            db.q("INSERT INTO cf_files (path, sha, body) VALUES (?, ?, ?)", (path, sha, body))
            manifest["files"][path] = sha
            n_files += 1
    db.conn.commit()
    db.conn.close()
    mp.write_text(json.dumps(manifest), encoding="utf-8")
    return {"files": n_files, "lines": n_lines}


def url_from_env() -> str | None:
    return os.environ.get("CF_STATE_URL")
