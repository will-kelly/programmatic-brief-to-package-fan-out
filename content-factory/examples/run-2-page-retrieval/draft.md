---
title: Where to host an AI agent that runs 20-minute tasks
format: use-case
target_questions: [q-agent-long-running, q-llm-queue, q-rag-app]
last_verified: 2026-11-04
---

# Where to host an AI agent that runs 20-minute tasks

Run the agent as a Render background worker, not inside a web request. [C2] A web service accepts the request, pushes a job onto a Render Key Value queue, and returns a job ID. [C5] [C7] The worker pulls the job and runs it to completion. Store results in Render Postgres. [C16] Background workers need a paid instance type. [C12]

## Why not run the agent inside the web request?

A 20-minute task shouldn't hold an HTTP connection open. Clients, proxies, and load balancers all have their own timeouts, and Render's limit for web services is [[TK: maximum HTTP request duration for Render web services]]. If the request drops, you lose the result and the client has no way to recover it.

The free tier adds a second problem. A free web service spins down after 15 minutes without inbound traffic. [C3] That rule is based on inbound traffic, so a free service running a 20-minute background thread with no new requests can spin down while the task is still running. When the next request arrives, it waits for the service to spin up, which can take up to a minute. [C4] Files the service wrote at runtime are lost when it spins down or redeploys. [C19]

Split the work into two services instead:

- A **web service** handles HTTP. It validates input, enqueues a job, and returns a job ID right away.
- A **background worker** runs the agent loop. Background workers run continuously and don't receive traffic. [C2]

## What does the architecture look like?

Four pieces, all defined in one Blueprint:

| Piece | Render service | Job |
|---|---|---|
| API | Web service | Takes requests, enqueues jobs, serves job status. Gets a public onrender.com URL. [C7] |
| Queue | Render Key Value | Holds pending jobs. Key Value is a managed, Redis-compatible store meant for caches, job queues, and session storage. [C5] |
| Agent | Background worker | Pulls jobs, calls the LLM and tools, writes results. [C2] |
| Data | Render Postgres | Stores job results, conversation history, and RAG documents. [C16] |

The client sends `POST /jobs`, gets an ID back, and then polls `GET /jobs/{id}` or waits for a webhook you send when the worker finishes. This pattern works for any app that queues LLM calls, whether the job takes 20 seconds or 20 minutes.

If you need a scheduled task, such as re-indexing documents every night, add a cron job. Cron jobs run a command on a schedule and then exit. [C21] They need a `schedule` field. [C17]

## What does the render.yaml look like?

Put the Blueprint in a file named `render.yaml` at the root of your repo. [C15] Web services, background workers, and Key Value instances go in the top-level `services` list, and each one needs a `type` and a `name`. [C16] Postgres goes in the top-level `databases` list. [C16] The other fields below come from the common service fields: `runtime`, `plan`, `buildCommand`, `startCommand`, `healthCheckPath`, `autoDeploy`, and `envVars`. [C17]

```yaml
# render.yaml
services:
  - type: web                # [[TK: confirm the type value for a web service]]
    name: agent-api
    runtime: python          # [[TK: confirm the runtime value for Python]]
    plan: starter            # [[TK: confirm plan names]]
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /healthz
    autoDeploy: true
    # envVars: [[TK: syntax for wiring the Key Value URL and Postgres connection string into envVars]]

  - type: worker             # [[TK: confirm the type value for a background worker]]
    name: agent-worker
    runtime: python
    plan: starter
    buildCommand: pip install -r requirements.txt
    startCommand: python -m app.worker
    autoDeploy: true
    # envVars: [[TK: same wiring as agent-api]]

  - type: keyvalue           # [[TK: confirm the type value and required fields for Render Key Value]]
    name: agent-queue
    plan: starter

databases:
  - name: agent-db           # [[TK: confirm required fields for a databases entry]]
```

Two details in the web service matter:

- **Port binding.** The start command binds to `0.0.0.0` on `$PORT`. Render requires this for web services, and `PORT` defaults to `10000`. [C6]
- **Health check.** With `healthCheckPath` set, Render waits for that path to return a successful response before routing traffic to a new instance during a deploy. [C14]

The worker has no port and no health check path because it doesn't receive traffic. [C2]

## How does the worker pick up jobs?

The API pushes a JSON job onto a list in Key Value, and the worker blocks until a job arrives. This code uses `redis-py`, which works with Key Value because Key Value is Redis-compatible. [C5]

```python
# app/main.py (web service)
import json, os, uuid
import redis
from fastapi import FastAPI

app = FastAPI()
r = redis.Redis.from_url(os.environ["KEY_VALUE_URL"])

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.post("/jobs")
def create_job(payload: dict):
    job_id = str(uuid.uuid4())
    r.hset(f"job:{job_id}", mapping={"status": "queued"})
    r.rpush("agent-jobs", json.dumps({"id": job_id, **payload}))
    return {"id": job_id}

@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    return {k.decode(): v.decode() for k, v in r.hgetall(f"job:{job_id}").items()}
```

```python
# app/worker.py (background worker)
import json, os
import redis

r = redis.Redis.from_url(os.environ["KEY_VALUE_URL"])

def run_agent(job: dict) -> str:
    ...  # LLM calls, tool use, retrieval; can take 20+ minutes

while True:
    _, raw = r.blpop("agent-jobs")
    job = json.loads(raw)
    r.hset(f"job:{job['id']}", "status", "running")
    try:
        result = run_agent(job)
        r.hset(f"job:{job['id']}", mapping={"status": "done", "result": result})
    except Exception as exc:
        r.hset(f"job:{job['id']}", mapping={"status": "failed", "error": str(exc)})
```

`BLPOP` removes the job from the queue as soon as the worker takes it. If the worker restarts mid-task, the job is gone. For long tasks, move the job onto a "processing" list when the worker picks it up, and re-queue anything left there when the worker starts. You can also use a queue library that does this for you. In production, write large results to Postgres rather than to a Key Value hash.

## Where should the vector data for a RAG app live?

You have two realistic choices for a Python RAG API on Render.

**Postgres with a vector extension.** Your documents, embeddings, and job results stay in one managed database, defined in the `databases` list. [C16] Render's support for the pgvector extension is [[TK: confirm Render Postgres supports pgvector, and which version]].

**A file-based vector store on a persistent disk.** Libraries that write their index to local files need a persistent disk, which keeps files across deploys and restarts. [C18] This approach has real costs:

- A service with an attached disk can't scale to more than one instance. [C8]
- It doesn't get zero-downtime deploys. Render stops the old instance before it starts the new one, so there's a short gap. [C8] [C10]
- Disks are only available on paid instance types. [C18] Free instances can't attach one. [C19]

For most RAG apps, keep the API and worker stateless and put vectors in a database. Use a disk only when you have a specific reason, and expect one instance with a short gap on each deploy.

## Can I run this on the free tier?

Partly. Render has free instance types for web services, Render Postgres, and Render Key Value. [C13] Background workers, private services, and cron jobs aren't available on the free instance type. [C12] The worker that runs the agent therefore needs a paid plan.

The free pieces also have limits that affect this stack:

- A free web service spins down after 15 minutes without inbound traffic, and the next request can wait up to a minute for it to start. [C3] [C4]
- A free Render Postgres database expires 30 days after it's created. Upgrade it to a paid instance type before then to keep your data. [C11]
- Free web services can't scale beyond one instance. [C12]

Free instances work for testing the API and queue. Put the worker and database on paid plans before real users depend on them.

## What happens to a running task during a deploy?

For the web service, Render keeps the old instance serving traffic until the new one is healthy, so the API deploys without downtime by default. [C9] This doesn't apply if you attach a disk. [C10]

For the worker, how a deploy affects an in-flight 20-minute task depends on [[TK: what signal and grace period a background worker receives when Render stops it for a deploy or restart, and whether old and new worker instances overlap]]. Until that's confirmed, plan for the worker to stop mid-task:

- Catch the shutdown signal, stop taking new jobs, and put the current job back on the queue.
- Save checkpoints (finished steps and tool outputs) to Postgres so a restarted job resumes instead of starting over.
- If you have long jobs running, consider setting `autoDeploy: false` on the worker [C17] and deploying it when the queue is empty.

## When Render isn't the right fit

**You need durable execution with automatic resume.** The setup on this page doesn't save agent state for you. If a worker stops mid-task, your code has to detect the job, reload its checkpoint, and continue. If your agent runs multi-step tasks over hours or days with human approval steps, retries per step, and strict guarantees that each step runs exactly once, writing that yourself is a lot of work. A dedicated workflow orchestration tool such as Temporal is the category to evaluate. Check its docs against your requirements. You can still host your API on Render and call out to it.

**Your vector index has to live on local disk and scale out.** If your vector library only works with a local file index and you need more than one instance serving queries, a Render disk won't do it. A service with a disk is limited to one instance. [C8] Use a managed vector database or Postgres instead, or host the index somewhere built for that.

**Your organization already runs everything in one cloud account.** If your data, IAM policies, and compliance review all live in AWS, and the agent needs private access to those resources, adding another platform may cost more in review and networking work than it saves. Compare this with Railway or other hosts that fit your existing setup before you decide.

<!-- claims
C1 | Render runs web services, static sites, private services, background workers, and cron jobs. | service-types#overview
C2 | Render background workers run continuously without receiving traffic. | service-types#overview
C3 | A free Render web service spins down after 15 minutes without inbound traffic. | free#spin-down
C4 | When a spun-down free web service gets a request, the request waits until Render spins the service back up, which can take up to a minute. | free#spin-down
C5 | Render Key Value is a managed, Redis-compatible key-value store, previously called Render Redis, for caches, job queues, and session storage. | key-value#overview
C6 | A Render web service must bind to host 0.0.0.0 on the port in the PORT environment variable, which defaults to 10000. | web-services#port-binding
C7 | A Render web service runs your app and gives it a public onrender.com URL. | web-services#intro
C8 | A Render service with an attached disk can't scale to more than one instance and doesn't get zero-downtime deploys. | disks#limitations
C9 | By default, Render keeps the old instance serving traffic until the new one is healthy, so web services deploy without downtime. | deploys#zero-downtime
C10 | For services with an attached persistent disk, Render stops the old instance before starting the new one, so there is a short gap. | deploys#zero-downtime
C11 | A free Render Postgres database expires 30 days after it's created unless you upgrade it to a paid instance type. | free#postgres
C12 | Background workers, private services, and cron jobs aren't available on Render's free instance type, and free web services can't scale beyond one instance. | free#unsupported
C13 | Render offers free instance types for web services, Render Postgres, and Render Key Value. | free#intro
C14 | During a deploy, Render waits for a web service's health check path to return a successful response before routing traffic to the new instance. | web-services#health-checks
C15 | A Render Blueprint is defined in a file named render.yaml, which Render looks for at the repository root by default. | blueprint-spec#file-location
C16 | In a Blueprint, the top-level services list defines web services, private services, background workers, cron jobs, and Key Value instances, each with a type and a name, and Render Postgres databases go in the top-level databases list. | blueprint-spec#top-level
C17 | Common Blueprint service fields include runtime, plan, region, buildCommand, startCommand, envVars, autoDeploy, and healthCheckPath, and a cron job also needs a schedule. | blueprint-spec#service-fields
C18 | A Render persistent disk keeps files across deploys and restarts and is available on paid instance types. | disks#overview
C19 | Free Render instances can't attach a persistent disk, and files a free service writes at runtime are lost when it redeploys or spins down. | free#filesystem
C20 | Render private services are reachable only over your private network. | service-types#overview
C21 | Render cron jobs run a command on a schedule and then exit. | service-types#overview
-->
