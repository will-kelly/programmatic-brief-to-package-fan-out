# Brief: Where should I host an AI agent that runs long tasks, sometimes for 20 minutes or more

**Gap:** BURIED. **Format:** use-case. **Issued:** 2026-11-04.

## Why this piece

BURIED on 3 question(s) in ai-agents, combined demand 13; severity 2 x demand / effort 2.0 = 13.0.

- `q-agent-long-running`: mentioned in 100% of 3 answers (95% CI 44%–100%); named instead: AWS (3/3), Vercel (3/3), Netlify (3/3); picked first in 0%, average rank 9.33; tentative on 3 samples: raise k for this question next survey
- `q-llm-queue`: mentioned in 100% of 3 answers (95% CI 44%–100%); named instead: Temporal (3/3), Inngest (3/3), Trigger.dev (3/3); picked first in 0%, average rank 5.67; tentative on 3 samples: raise k for this question next survey
- `q-rag-app`: mentioned in 100% of 3 answers (95% CI 44%–100%); named instead: Railway (3/3), Fly.io (3/3), Google Cloud Run (3/3); picked first in 33%, average rank 1.33; tentative on 3 samples: raise k for this question next survey

## Questions it has to answer

- `q-agent-long-running` Where should I host an AI agent that runs long tasks, sometimes for 20 minutes or more?
- `q-llm-queue` What's a good architecture and host for an app that queues LLM calls and processes them in the background?
- `q-rag-app` Where should I deploy a RAG app with a vector database and a Python API?

## Angle

Go narrower than existing coverage: this exact stack or use case, with a working render.yaml and the decisions a developer actually faces.

## Sources to build from

- `disks#limitations`: Limitations
- `free#spin-down`: Spin-down behavior
- `key-value#overview`: Overview
- `web-services#port-binding`: Port binding
- `free#postgres`: Free Postgres
- `deploys#zero-downtime`: Zero-downtime deploys

## How it will be checked

Run `cf check your-draft.md --brief this-brief.md` before you send it. The checker runs the same checks on every draft, in-house or partner:

- 0 contradicted claims and 0 lint errors from `cf check`
- every claim about Render tagged and tied to a docs section
- answer to the lead question in the first 60 words
- a 'When Render isn't the right fit' section with a real case
- no factual claims about competitors beyond what this brief supplies

## Machine-readable brief

```json
{
  "id": "where-should-i-host-an-ai-agent-that-runs-long-tasks-sometim",
  "title": "Where should I host an AI agent that runs long tasks, sometimes for 20 minutes or more",
  "format": "use-case",
  "gap": "BURIED",
  "questions": [
    "q-agent-long-running",
    "q-llm-queue",
    "q-rag-app"
  ],
  "questions_text": [
    "Where should I host an AI agent that runs long tasks, sometimes for 20 minutes or more?",
    "What's a good architecture and host for an app that queues LLM calls and processes them in the background?",
    "Where should I deploy a RAG app with a vector database and a Python API?"
  ],
  "angle": "Go narrower than existing coverage: this exact stack or use case, with a working render.yaml and the decisions a developer actually faces.",
  "must_cite": [
    "disks#limitations",
    "free#spin-down",
    "key-value#overview",
    "web-services#port-binding",
    "free#postgres",
    "deploys#zero-downtime"
  ],
  "named_instead": [
    "AWS",
    "Railway",
    "Temporal"
  ],
  "acceptance": [
    "0 contradicted claims and 0 lint errors from `cf check`",
    "every claim about Render tagged and tied to a docs section",
    "answer to the lead question in the first 60 words",
    "a 'When Render isn't the right fit' section with a real case",
    "no factual claims about competitors beyond what this brief supplies"
  ],
  "issued": "2026-11-04"
}
```
