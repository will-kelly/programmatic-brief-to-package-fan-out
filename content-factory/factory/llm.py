"""Model calls. One function, `ask`, with swappable backends.

  CF_LLM=claude-cli  (default) headless `claude -p` with tools switched off.
                     Good on a laptop where Claude Code is logged in.
  CF_LLM=anthropic   the Messages API through the `anthropic` SDK. Use this
                     in production (Render Workflows). Needs ANTHROPIC_API_KEY.
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
    elif backend == "anthropic":
        r = _anthropic(prompt, system, model, role, timeout)
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


# --------------------------------------------------------------------------
# Messages API backend

DEFAULT_MODEL = "claude-opus-5-5"
# $ per million tokens: input, output, cache read, cache write (5-minute).
# Used to log an estimated cost per call; check current prices before you
# budget from these.
PRICES = {
    "claude-opus-5-5": (4.00, 20.00, 0.20, 5.00),
    "claude-sonnet-5-5": (2.00, 10.00, 0.20, 2.50),
    "claude-haiku-5-5": (0.10, 0.50, 0.01, 0.125),
}
# Effort per role. Claude Opus 5.5 defaults to "medium", so set it on
# purpose: drafting gets more thought than answering a survey question.
# Override any role with CF_EFFORT_<ROLE>, e.g. CF_EFFORT_CLAIM_JUDGE=high.
EFFORT = {"draft": "high", "claim-judge": "medium", "survey-judge": "medium",
          "claim-extract": "medium", "survey-answer": "medium"}

_client = None


def _get_client():
    global _client
    if _client is None:
        try:
            import anthropic  # only needed for this backend
        except ImportError:
            raise SystemExit("CF_LLM=anthropic needs the SDK: pip install -r requirements.txt")
        _client = anthropic.Anthropic(max_retries=4, timeout=600.0)
    return _client


def estimate_cost(model: str, usage) -> float:
    pin, pout, pread, pwrite = PRICES.get(model, PRICES[DEFAULT_MODEL])
    get = lambda k: getattr(usage, k, 0) or 0
    return round((get("input_tokens") * pin + get("output_tokens") * pout
                  + get("cache_read_input_tokens") * pread
                  + get("cache_creation_input_tokens") * pwrite) / 1e6, 6)


class Refused(RuntimeError):
    pass


def _anthropic(prompt: str, system: str, model: str | None, role: str, timeout: int) -> Reply:
    model = model or DEFAULT_MODEL
    effort = os.environ.get("CF_EFFORT_" + role.upper().replace("-", "_"), EFFORT.get(role, "medium"))
    try:
        resp = _create(model, system, prompt, effort, timeout)
    except TypeError as e:
        if "authentication" in str(e):
            raise SystemExit("CF_LLM=anthropic found no credentials: set ANTHROPIC_API_KEY "
                             "(or log in with `ant auth login`)")
        raise
    if resp.stop_reason == "refusal":
        cat = getattr(resp.stop_details, "category", None) if resp.stop_details else None
        raise Refused(f"model declined ({cat or 'no category'}) for role {role}")
    text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    if resp.stop_reason == "max_tokens":
        text += "\n[[TK: response cut off at max_tokens]]"
    return Reply(text, estimate_cost(resp.model, resp.usage), 0.0, resp.model)


def _create(model, system, prompt, effort, timeout):
    return _get_client().with_options(timeout=float(timeout)).beta.messages.create(
        model=model,
        max_tokens=16000,
        # Judge and drafting prompts are fixed per role, so cache them.
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": prompt}],
        thinking={"type": "adaptive"},
        output_config={"effort": effort},
        # Server-side fallback: if a safety classifier declines (it can
        # misfire on security-adjacent infra questions), the API reruns the
        # request on a fallback model instead of returning nothing.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    )
