"""Model calls. One function, `ask`, with swappable backends.

  CF_LLM=claude-cli  (default) headless `claude -p` with tools switched off
  CF_LLM=fake        deterministic stand-in for tests and offline evals

Every call returns the text plus cost and timing, and every call is logged
to state/llm-calls.jsonl, so the metrics job can report cost per piece and
the eval job can tell whether a prompt change moved spend.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass

from .common import STATE, append_jsonl, sha


@dataclass
class Reply:
    text: str
    cost_usd: float = 0.0
    duration_s: float = 0.0
    model: str = ""


def ask(prompt: str, system: str = "You are a helpful assistant.", *, role: str = "general",
        model: str | None = None, timeout: int = 300) -> Reply:
    backend = os.environ.get("CF_LLM", "claude-cli")
    model = model or os.environ.get("CF_MODEL") or None
    t0 = time.time()
    if backend == "fake":
        from . import fake_llm
        r = Reply(fake_llm.respond(role, prompt, system), 0.0, 0.0, "fake")
    elif backend == "claude-cli":
        r = _claude_cli(prompt, system, model, timeout)
    else:
        raise SystemExit(f"unknown CF_LLM backend '{backend}'")
    r.duration_s = round(time.time() - t0, 2)
    append_jsonl(STATE / "llm-calls.jsonl", [{
        "ts": int(t0), "role": role, "backend": backend, "model": r.model,
        "prompt_sha": sha(system + "\n" + prompt), "cost_usd": r.cost_usd,
        "duration_s": r.duration_s,
    }])
    return r


def _claude_cli(prompt: str, system: str, model: str | None, timeout: int) -> Reply:
    # The prompt goes on stdin: a draft that opens with "---" front matter
    # would otherwise parse as a flag, and long source packs hit argv limits.
    cmd = [os.environ.get("CF_CLAUDE", "claude"), "-p",
           "--system-prompt", system, "--tools", "", "--strict-mcp-config",
           "--no-session-persistence", "--output-format", "json"]
    if model:
        cmd += ["--model", model]
    last = None
    for attempt in range(3):
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, input=prompt)
            d = json.loads(out.stdout)
            if d.get("is_error"):
                raise RuntimeError(d.get("result", "claude returned an error"))
            used = next(iter(d.get("modelUsage", {}) or {}), model or "default")
            return Reply(d.get("result", ""), float(d.get("total_cost_usd", 0.0)), 0.0, used)
        except (subprocess.TimeoutExpired, json.JSONDecodeError, RuntimeError) as e:
            last = e
            time.sleep(2 ** attempt)
    raise RuntimeError(f"claude call failed after 3 attempts: {last}")
