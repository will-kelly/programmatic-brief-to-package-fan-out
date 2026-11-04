---
title: Hosting an AI agent that runs 20-minute tasks on Render
format: use-case
target_questions: [q-agent-long-running, q-llm-queue, q-rag-app]
last_verified: 2026-11-04
---

# Hosting an AI agent that runs 20-minute tasks on Render

Run the agent as a Render background worker, not inside a web request. A small web service accepts each task and pushes it onto a Render Key Value queue. The worker pulls jobs off that queue and runs them. Background workers run continuously without receiving traffic [C1], and Key Value is built for job queues. [C5]

## Where should I run a task that takes 20 minutes or more?

Run it in a background worker. Render has five service types: web services, static sites, private services, background workers, and cron jobs. [C2] Each one fits a different part of an agent app:

| Part of the app | Service type | Why |
| --- | --- | --- |
| API that accepts tasks and returns status | Web service | Web services are reachable from the public internet [C3] and get a public onrender.com URL. [C8] |
| Agent loop that calls the LLM and tools | Background worker | It runs continuously and doesn't receive traffic. [C1] |
| Internal service, such as a self-hosted vector store | Private service | It's reachable only over your private network. [C3] |
| Nightly re-indexing or cleanup | Cron job | It runs a command on a schedule and then exits. [C4] |

Don't hold an HTTP request open while the agent works. The request ties up a web instance and fails if the client disconnects. It may also hit a request timeout: [[TK: Render's maximum HTTP request duration for web services]]. Return a job ID right away and let the client poll or subscribe for the result.

Also check how long a single worker job can run before you design around 20-minute or longer tasks: [[TK: any maximum run time or idle limit for background workers]].

## What's a good architecture for queuing LLM calls in the background?

Use four pieces:

1. **Web service (API).** It validates the request, writes a job record, pushes the job ID onto a queue, and returns `202` with the ID.
2. **Render Key Value (queue).** It's a managed, Redis-compatible key-value store, formerly called Render Redis, meant for caches, job queues, and session storage. [C5] [C6] Because it's Redis-compatible, any Redis client or Redis-backed queue library works with it.
3. **Background worker.** It blocks on the queue, runs the agent, and writes progress and results back.
4. **Render Postgres.** It stores the job records, results, and app data.

To process more tasks at once, add worker instances. Each instance pulls its own jobs from the shared queue. To rate-limit LLM calls across all workers, keep a counter or token bucket in the same Key Value instance.

A minimal worker loop with `redis-py`:

```python
import json
import os

import redis

# Set REDIS_URL to your Key Value instance's connection URL.
# [[TK: the env var name or Blueprint reference Render uses to expose the Key Value connection string]]
r = redis.Redis.from_url(os.environ["REDIS_URL"])


def run_agent(job: dict) -> dict:
    # Call your LLM and tools here. This can take 20+ minutes.
    ...


while True:
    # Block until a job is available.
    _, raw = r.blpop("agent:jobs")
    job = json.loads(raw)
    r.hset(f"agent:job:{job['id']}", mapping={"status": "running"})
    try:
        result = run_agent(job)
        r.hset(
            f"agent:job:{job['id']}",
            mapping={"status": "done", "result": json.dumps(result)},
        )
    except Exception as exc:
        r.hset(
            f"agent:job:{job['id']}",
            mapping={"status": "failed", "error": str(exc)},
        )
```

`blpop` removes the job from the queue as soon as a worker picks it up. If the worker dies partway through, that job is lost. For tasks that run 20 minutes, use a queue library that supports acknowledgments and retries, or move the job to an "in progress" list and requeue it if it goes stale.

## What does the render.yaml look like?

A Blueprint defines web services, private services, background workers, cron jobs, and Key Value instances in the top-level `services` list. Each service needs a `type` and a `name`. [C15] Render Postgres databases go in the top-level `databases` list. [C16] Environment groups go under `envVarGroups`. [C17]

The source pack for this page covers only those fields. The skeleton below shows the structure. Each `[[TK]]` marks a value or field you need to fill in from the Blueprint reference before you deploy.

```yaml
services:
  - type: "[[TK: Blueprint type value for a web service]]"
    name: agent-api
    # [[TK: runtime, build command, start command, and plan fields for a Python web service]]

  - type: "[[TK: Blueprint type value for a background worker]]"
    name: agent-worker
    # [[TK: runtime, build command, start command, and plan fields for a Python worker]]

  - type: "[[TK: Blueprint type value for a Key Value instance]]"
    name: agent-queue
    # [[TK: fields for Key Value plan and access settings]]

databases:
  - name: agent-db
    # [[TK: confirm the required fields for a databases entry]]

# Put shared settings, such as LLM API keys, in an environment group
# so the API and the worker read the same values.
envVarGroups:
  # [[TK: fields for an envVarGroups entry, and how services reference it]]
```

## How do I make the Python API listen on the right port?

Bind to host `0.0.0.0` on the port in the `PORT` environment variable. The default `PORT` is `10000`. [C7]

```python
import os

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "10000")),
    )
```

The worker doesn't receive traffic [C1], so it doesn't need to bind a port.

## Where should I deploy a RAG app with a vector database and a Python API?

Use the same layout. The Python API runs as a web service. Ingestion and embedding jobs run on a background worker that reads from the Key Value queue. Scheduled re-indexing runs as a cron job. [C4]

For the vector store itself, you have two options:

- **Vectors in Render Postgres.** One database holds both your app data and your embeddings. [[TK: whether Render Postgres supports the pgvector extension, and on which versions]]
- **A self-hosted vector database as a private service.** It's reachable only over your private network [C3], so the store isn't exposed to the internet. Most vector databases need a persistent disk, and a disk brings two limits. A service with an attached disk can't scale beyond one instance, and it doesn't get zero-downtime deploys. [C12]

If Postgres covers your vector search needs, pick it. It avoids the disk limits on your retrieval path.

## Can I prototype this on free instances?

Yes, for testing. Render offers free instance types for web services, Render Postgres, and Render Key Value. [C18] Two free-tier behaviors matter for this stack:

- **Spin-down.** A free web service spins down after 15 minutes without inbound traffic. [C9] The next request waits while Render spins it back up, which can take up to a minute. [C10] Clients polling for job status will see that delay after quiet periods.
- **Database expiry.** A free Render Postgres database expires 30 days after it's created. Upgrade it to a paid instance type before then to keep your data. [C11] Don't store job history or embeddings you can't rebuild in a free database.

[[TK: whether background workers have a free instance type]]

## What happens to a running agent task when I deploy?

By default, Render keeps the old instance serving traffic until the new one is healthy, so web services deploy without downtime. [C13] That protects your API.

Services with an attached persistent disk are the exception. Render stops the old instance before starting the new one, so there's a short gap. [C14] Keep disks off the API and the worker if you can.

For the worker, the question is what happens to a job that's 15 minutes in when a deploy starts. [[TK: how Render stops a background worker instance during a deploy, including the shutdown signal and grace period]] Plan on interruptions either way. Make jobs resumable or safe to retry, save progress to Postgres or Key Value as the agent works, and requeue jobs that never finish.

## When Render isn't the right fit

**You need a self-hosted vector database or agent state on local disk, and you need it to scale out.** A service with an attached disk runs on a single instance and doesn't get zero-downtime deploys. [C12] If your retrieval layer needs several instances behind it, or can't accept a short gap on every deploy [C14], a disk-backed service on Render won't do that. Use a managed vector store instead. Compare the tradeoffs in the docs for that store or for a provider such as AWS.

**Your agent is really a long, multi-step workflow that must survive crashes partway through.** A queue and a worker work well when a job can be retried from the start or from a saved checkpoint. If you need step-level durability, replay, and visibility into each step of an hours-long process, look at a workflow engine such as Temporal. You can still run your API on Render next to it.

If you're comparing general-purpose hosts, Railway is another option developers often consider. Check its current docs for worker, queue, and database support before you decide.

<!-- claims
C1 | Render background workers run continuously without receiving traffic. | service-types#overview
C2 | Render runs web services, static sites, private services, background workers, and cron jobs. | service-types#overview
C3 | Render web services and static sites are reachable from the public internet, while private services are reachable only over your private network. | service-types#overview
C4 | Render cron jobs run a command on a schedule and then exit. | service-types#overview
C5 | Render Key Value is a managed, Redis-compatible key-value store for caches, job queues, and session storage. | key-value#overview
C6 | Render Key Value was previously called Render Redis. | key-value#overview
C7 | A Render web service must bind to host 0.0.0.0 on the port in the PORT environment variable, which defaults to 10000. | web-services#port-binding
C8 | A Render web service runs your app and gives it a public onrender.com URL. | web-services#intro
C9 | A free Render web service spins down after 15 minutes without inbound traffic. | free#spin-down
C10 | When a spun-down free web service receives a request, the request waits while Render spins it back up, which can take up to a minute. | free#spin-down
C11 | A free Render Postgres database expires 30 days after it's created and must be upgraded to a paid instance type before then to keep its data. | free#postgres
C12 | A Render service with an attached disk can't scale to more than one instance and doesn't get zero-downtime deploys. | disks#limitations
C13 | By default, Render keeps the old instance serving traffic until the new one is healthy, so web services deploy without downtime. | deploys#zero-downtime
C14 | For services with an attached persistent disk, Render stops the old instance before starting the new one, causing a short gap. | deploys#zero-downtime
C15 | The top-level services list in a Render Blueprint defines web services, private services, background workers, cron jobs, and Key Value instances, and each service needs a type and a name. | blueprint-spec#top-level
C16 | Render Postgres databases are defined in the top-level databases list of a Blueprint. | blueprint-spec#top-level
C17 | Environment groups are defined under envVarGroups in a Render Blueprint. | blueprint-spec#top-level
C18 | Render offers free instance types for web services, Render Postgres, and Render Key Value, for hobby projects and testing. | free#intro
-->
