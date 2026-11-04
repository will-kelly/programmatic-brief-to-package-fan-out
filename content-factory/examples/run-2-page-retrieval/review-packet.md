# Review packet: where-should-i-host-an-ai-agent-that-runs-long-tasks-sometimes-for-20-minutes-or-more

Brief: Where should I host an AI agent that runs long tasks, sometimes for 20 minutes or more (use-case), targets q-agent-long-running, q-llm-queue, q-rag-app

**0 claims need you.** 0 verified against the docs, 21 corroborated by seed facts only, 0 lint errors. Estimated review time 14.5 minutes (about 52.0 without the checker).

## Open TKs

The writer stopped instead of guessing. Each of these is a fact the docs snapshot doesn't state. They also go to the docs-gap report (`cf docs gaps`).

- maximum HTTP request duration for Render web services
- confirm the type value for a web service
- confirm the runtime value for Python
- confirm plan names
- syntax for wiring the Key Value URL and Postgres connection string into envVars
- confirm the type value for a background worker
- same wiring as agent-api
- confirm the type value and required fields for Render Key Value
- confirm required fields for a databases entry
- confirm Render Postgres supports pgvector, and which version
- what signal and grace period a background worker receives when Render stops it for a deploy or restart, and whether old and new worker instances overlap

## Untracked claims

These sentences read like claims about Render but carry no claim tag, so nothing checked them.

- A free Render Postgres database expires 30 days after it's created.

## Corroborated only (spot-check one)

- C1: Render runs web services, static sites, private services, background workers, and cron jobs. (service-types#overview)
- C2: Render background workers run continuously without receiving traffic. (service-types#overview)
- C3: A free Render web service spins down after 15 minutes without inbound traffic. (free#spin-down)
- C4: When a spun-down free web service gets a request, the request waits until Render spins the service back up, which can take up to a minute. (free#spin-down)
- C5: Render Key Value is a managed, Redis-compatible key-value store, previously called Render Redis, for caches, job queues, and session storage. (key-value#overview)
- C6: A Render web service must bind to host 0.0.0.0 on the port in the PORT environment variable, which defaults to 10000. (web-services#port-binding)
- C7: A Render web service runs your app and gives it a public onrender.com URL. (web-services#intro)
- C8: A Render service with an attached disk can't scale to more than one instance and doesn't get zero-downtime deploys. (disks#limitations)
- C9: By default, Render keeps the old instance serving traffic until the new one is healthy, so web services deploy without downtime. (deploys#zero-downtime)
- C10: For services with an attached persistent disk, Render stops the old instance before starting the new one, so there is a short gap. (deploys#zero-downtime)
- C11: A free Render Postgres database expires 30 days after it's created unless you upgrade it to a paid instance type. (free#postgres)
- C12: Background workers, private services, and cron jobs aren't available on Render's free instance type, and free web services can't scale beyond one instance. (free#unsupported)
- C13: Render offers free instance types for web services, Render Postgres, and Render Key Value. (free#intro)
- C14: During a deploy, Render waits for a web service's health check path to return a successful response before routing traffic to the new instance. (web-services#health-checks)
- C15: A Render Blueprint is defined in a file named render.yaml, which Render looks for at the repository root by default. (blueprint-spec#file-location)
- C16: In a Blueprint, the top-level services list defines web services, private services, background workers, cron jobs, and Key Value instances, each with a type and a name, and Render Postgres databases go in the top-level databases list. (blueprint-spec#top-level)
- C17: Common Blueprint service fields include runtime, plan, region, buildCommand, startCommand, envVars, autoDeploy, and healthCheckPath, and a cron job also needs a schedule. (blueprint-spec#service-fields)
- C18: A Render persistent disk keeps files across deploys and restarts and is available on paid instance types. (disks#overview)
- C19: Free Render instances can't attach a persistent disk, and files a free service writes at runtime are lost when it redeploys or spins down. (free#filesystem)
- C20: Render private services are reachable only over your private network. (service-types#overview)
- C21: Render cron jobs run a command on a schedule and then exit. (service-types#overview)

## When you're done

```bash
cf review done <run-dir> --minutes <n> --corrections <n>
```

Every correction you make that the checker passed becomes an eval case, so the checker learns what it missed.
