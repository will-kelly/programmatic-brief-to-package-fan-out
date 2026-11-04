"""Small shared helpers: paths, config, JSON lines, hashing, slugs."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import tomllib
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(os.environ.get("CF_ROOT", Path(__file__).resolve().parent.parent))
CONFIG = Path(os.environ.get("CF_CONFIG", ROOT / "config"))
STATE = Path(os.environ.get("CF_STATE", ROOT / "state"))


def load_toml(name: str) -> dict:
    p = Path(name) if Path(name).is_file() else CONFIG / name
    return tomllib.loads(p.read_text(encoding="utf-8"))


def now_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def sha(text: str | bytes, n: int = 12) -> str:
    if isinstance(text, str):
        text = text.encode("utf-8")
    return hashlib.sha256(text).hexdigest()[:n]


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "untitled"


def read_jsonl(p: Path) -> list[dict]:
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def append_jsonl(p: Path, rows) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def write_json(p: Path, data) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(p: Path, default=None):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson interval for a rate. With 3 samples a question, a single
    answer is an anecdote; the interval says how much the rate can move."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, (c - m) / d), min(1.0, (c + m) / d))


def pct(x: float) -> str:
    return f"{round(100 * x)}%"


def extract_json(text: str):
    """Pull the first JSON object or array out of a model reply."""
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if m:
        text = m.group(1)
    for opener, closer in (("[", "]"), ("{", "}")):
        i, j = text.find(opener), text.rfind(closer)
        if i != -1 and j > i:
            try:
                return json.loads(text[i : j + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError("no JSON in model reply")
