# Review packet: where-should-i-host-an-ai-agent-that-runs-long-tasks-sometimes-for-20-minutes-or-more

Brief: Where should I host an AI agent that runs long tasks, sometimes for 20 minutes or more (use-case), targets q-agent-long-running, q-llm-queue, q-rag-app

**0 claims need you.** 0 verified against the docs, 18 corroborated by seed facts only, 0 lint errors. Estimated review time 13.0 minutes (about 46.0 without the checker).

## Open TKs

The writer stopped instead of guessing. Each of these is a fact the docs snapshot doesn't state. They also go to the docs-gap report (`cf docs gaps`).

- Render's maximum HTTP request duration for web services
- any maximum run time or idle limit for background workers
- the env var name or Blueprint reference Render uses to expose the Key Value connection string
- Blueprint type value for a web service
- runtime, build command, start command, and plan fields for a Python web service
- Blueprint type value for a background worker
- runtime, build command, start command, and plan fields for a Python worker
- Blueprint type value for a Key Value instance
- fields for Key Value plan and access settings
- confirm the required fields for a databases entry
- fields for an envVarGroups entry, and how services reference it
- whether Render Postgres supports the pgvector extension, and on which versions
- whether background workers have a free instance type
- how Render stops a background worker instance during a deploy, including the shutdown signal and grace period

## Untracked claims

These sentences read like claims about Render but carry no claim tag, so nothing checked them.

- Database expiry.** A free Render Postgres database expires 30 days after it's created.

## Corroborated only (spot-check one)

- C1: Render background workers run continuously without receiving traffic. (service-types#overview)
- C2: Render runs web services, static sites, private services, background workers, and cron jobs. (service-types#overview)
- C3: Render web services and static sites are reachable from the public internet, while private services are reachable only over your private network. (service-types#overview)
- C4: Render cron jobs run a command on a schedule and then exit. (service-types#overview)
- C5: Render Key Value is a managed, Redis-compatible key-value store for caches, job queues, and session storage. (key-value#overview)
- C6: Render Key Value was previously called Render Redis. (key-value#overview)
- C7: A Render web service must bind to host 0.0.0.0 on the port in the PORT environment variable, which defaults to 10000. (web-services#port-binding)
- C8: A Render web service runs your app and gives it a public onrender.com URL. (web-services#intro)
- C9: A free Render web service spins down after 15 minutes without inbound traffic. (free#spin-down)
- C10: When a spun-down free web service receives a request, the request waits while Render spins it back up, which can take up to a minute. (free#spin-down)
- C11: A free Render Postgres database expires 30 days after it's created and must be upgraded to a paid instance type before then to keep its data. (free#postgres)
- C12: A Render service with an attached disk can't scale to more than one instance and doesn't get zero-downtime deploys. (disks#limitations)
- C13: By default, Render keeps the old instance serving traffic until the new one is healthy, so web services deploy without downtime. (deploys#zero-downtime)
- C14: For services with an attached persistent disk, Render stops the old instance before starting the new one, causing a short gap. (deploys#zero-downtime)
- C15: The top-level services list in a Render Blueprint defines web services, private services, background workers, cron jobs, and Key Value instances, and each service needs a type and a name. (blueprint-spec#top-level)
- C16: Render Postgres databases are defined in the top-level databases list of a Blueprint. (blueprint-spec#top-level)
- C17: Environment groups are defined under envVarGroups in a Render Blueprint. (blueprint-spec#top-level)
- C18: Render offers free instance types for web services, Render Postgres, and Render Key Value, for hobby projects and testing. (free#intro)

## When you're done

```bash
cf review done <run-dir> --minutes <n> --corrections <n>
```

Every correction you make that the checker passed becomes an eval case, so the checker learns what it missed.
