"""Agent traffic and citation signals.

AI crawler traffic isn't one number. The user agent says which lever a hit
pulls, and the levers need different fixes:

  training     GPTBot, ClaudeBot, CCBot, ...: shapes what the next model
               knows. Slow, broad. Fix: be crawlable, be correct.
  index        OAI-SearchBot, PerplexityBot, Claude-SearchBot: decides
               whether a page can be retrieved at answer time.
  live-fetch   ChatGPT-User, Claude-User, Perplexity-User: an assistant is
               reading this page right now to answer someone. The closest
               thing to a citation you can see in your own logs.
  agent        coding agents and HTTP libraries pulling raw docs (markdown
               twins, llms.txt). Developers' tools reading the docs.

A page with live-fetch hits and no citations has a content problem. A page
with no index hits has a discoverability problem, and writing more content
won't fix it.
"""

from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

CLASSES = [
    ("live-fetch", r"ChatGPT-User|Claude-User|Perplexity-User|MistralAI-User|Gemini-User|DuckAssistBot"),
    ("index", r"OAI-SearchBot|PerplexityBot|Claude-SearchBot|YouBot|Applebot(?!-Extended)|Bingbot|Googlebot"),
    ("training", r"GPTBot|ClaudeBot|anthropic-ai|CCBot|Google-Extended|Applebot-Extended|Bytespider|meta-externalagent|Amazonbot|cohere-ai"),
    ("agent", r"claude-code|Cursor|Codex|aider|python-httpx|python-requests|node-fetch|undici|axios|Go-http-client|curl/"),
]
LOG_RE = re.compile(r'^(\S+) \S+ \S+ \[([^\]]+)\] "(?:GET|HEAD) (\S+) [^"]*" (\d{3}) \S+ "[^"]*" "([^"]*)"')


def classify(ua: str) -> str | None:
    for name, pat in CLASSES:
        if re.search(pat, ua, re.I):
            return name
    return None


def norm_path(p: str) -> str:
    p = p.split("?", 1)[0].rstrip("/") or "/"
    return re.sub(r"\.md$", "", p)


def traffic(log: Path) -> dict:
    """Combined-format access log -> per-path counts by agent class."""
    per = defaultdict(Counter)
    errors = Counter()
    total = Counter()
    for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
        m = LOG_RE.match(line)
        if not m:
            continue
        _, _, path, status, ua = m.groups()
        cls = classify(ua)
        if not cls:
            continue
        path = norm_path(path)
        total[cls] += 1
        if status.startswith(("4", "5")):
            errors[(path, cls, status)] += 1
            continue
        per[path][cls] += 1
    return {"by_path": {p: dict(c) for p, c in per.items()}, "totals": dict(total),
            "errors": [{"path": p, "class": c, "status": s, "hits": n} for (p, c, s), n in errors.most_common(20)]}


def citations(csv_path: Path) -> list[dict]:
    """Citation exports from a tracker or a search-enabled survey:
    columns question_id, engine, cited_url (extra columns ignored)."""
    with csv_path.open(newline="", encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if r.get("question_id") and r.get("cited_url")]
