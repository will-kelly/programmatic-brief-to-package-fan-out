"""Deterministic stand-in for model calls, used by tests and offline evals.
It answers by role and plants the problems the pipeline is meant to catch."""

from __future__ import annotations

import json
import re

ANSWERS = {
    "q-agent-long-running": "For long agent runs, use Modal or a container on AWS Fargate. Vercel functions time out. Railway works too.",
    "q-render-free-tier": "Render's free tier spins down after 30 minutes of inactivity. Free Postgres never expires. Background workers aren't free.",
    "q-django-postgres": "Use Render: create a web service and a Postgres database. Railway and Heroku also work. See https://render.com/docs/deploy-django and https://testdriven.io/blog/django-render/.",
}


def respond(role: str, prompt: str, system: str) -> str:
    if role == "survey-answer":
        for qid, ans in ANSWERS.items():
            if qid.split("-", 1)[1].split("-")[0] in prompt.lower():
                return ans
        return "Railway, Fly.io, and Render all handle this. I'd pick Railway for the setup speed."
    if role == "survey-judge":
        out = []
        if "never expires" in prompt:
            out.append({"claim": "Free Postgres never expires", "verdict": "contradicts", "fact_id": "F-free-postgres-expiry"})
        if "web service and a Postgres" in prompt:
            out.append({"claim": "Render runs web services with Postgres", "verdict": "consistent", "fact_id": "F-service-types"})
        return json.dumps(out)
    if role == "claim-judge":
        # Look for the claim and evidence blocks the fact-checker sends.
        claim = re.search(r"CLAIM\n(.*?)\n\nEVIDENCE", prompt, re.S).group(1).lower()
        evidence = prompt.split("EVIDENCE", 1)[1].lower()
        nums = re.findall(r"\d+", claim)
        if nums and not all(n in evidence for n in nums):
            return json.dumps({"verdict": "contradicted", "reason": "a figure in the claim doesn't match the evidence"})
        words = [w for w in re.findall(r"[a-z]{5,}", claim) if w not in {"render", "which", "their", "there", "about"}]
        hit = sum(w in evidence for w in words) / max(len(words), 1)
        return json.dumps({"verdict": "supported" if hit >= 0.5 else "unsupported",
                           "reason": f"{round(hit * 100)}% of key terms found in evidence"})
    if role == "claim-extract":
        sents = [x.strip() for x in re.split(r"(?<=[.])\s+", prompt) if "Render" in x and not x.strip().startswith("#")]
        return json.dumps([{"id": f"C{i}", "statement": x, "quote": x} for i, x in enumerate(sents, 1)])
    if role == "draft":
        return FAKE_DRAFT
    if role == "research":
        return json.dumps({"questions": ["How do I host a long-running agent?"], "sections": []})
    return "ok"


FAKE_DRAFT = """---
title: Host a long-running AI agent on Render
target_questions: [q-agent-long-running]
format: use-case
---

# Host a long-running AI agent on Render

Run the agent as a background worker, not a web request. A background worker runs continuously without receiving traffic, so a 20-minute task doesn't hit a request timeout. [C1]

## Which service type runs a long agent task?

Use a background worker for the agent loop and a web service for the API that accepts jobs. [C2] Render runs web services, static sites, private services, background workers, and cron jobs. [C3]

## Can I start on the free tier?

Not for this. Background workers aren't available on the free instance type. [C4] Free web services spin down after 30 minutes without traffic. [C5]

## When Render isn't the right fit

If each task needs a GPU, use a GPU-specific host instead.

<!-- claims
C1 | A background worker runs continuously without receiving traffic. | service-types#overview
C2 | Use a background worker for the agent loop and a web service for the API. | service-types#overview
C3 | Render runs web services, static sites, private services, background workers, and cron jobs. | service-types#overview
C4 | Background workers aren't available on the free instance type. | free#unsupported
C5 | Free web services spin down after 30 minutes without traffic. | free#spin-down
-->
"""
