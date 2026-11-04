---
title: Run a background worker for an LLM queue
format: use-case
target_questions: [q-llm-queue]
last_verified: 2026-11-04
expect_flagged: C2
expect_lint:
---

# Run a background worker for an LLM queue

Put LLM calls on a queue and process them in a background worker, so a slow model call never holds a web request open. A background worker runs continuously without receiving traffic. [C1]

## Can I prototype this for free?

You can run the worker on the free instance type while you prototype. [C2]

## Where does the queue live?

Use Render Key Value, a managed Redis-compatible store, as the queue. [C3]

## When Render isn't the right fit

If each job needs a GPU, run inference on a GPU host and keep only the orchestration here.

<!-- claims
C1 | A background worker runs continuously without receiving traffic. | service-types#overview
C2 | A background worker can run on the free instance type. | free#unsupported
C3 | Render Key Value is a managed Redis-compatible store. | key-value#overview
-->
