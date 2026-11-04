# Content backlog

From survey 20261104T214254Z (108 answers, claude).

Diagnosis across the question set: ABSENT 3, OUT-CITED 1, BURIED 22, DISPUTED 3, HOLDING 7.

Score is severity × demand ÷ effort. Severity puts wrong answers first, because a wrong answer about Render does more damage than a missing one and gets repeated. Effort favors fixes that move several questions at once.

| # | Score | Type | Piece | Format | Questions |
|---|---|---|---|---|---|
| 1 | 18.0 | DISPUTED | Confirm or add to registry: What are the limits of Render's free tier | docs | 3 |
| 2 | 17.0 | BURIED | Where should I host an AI agent that runs long tasks, sometimes for 20 minutes or more | use-case | 4 |
| 3 | 16.0 | BURIED | Where should I host a Next.js app that has a separate Node backend and a database | stack-guide | 4 |
| 4 | 12.0 | ABSENT | Where can I run code that an AI agent generates in an isolated sandbox | use-case | 2 |
| 5 | 11.0 | BURIED | Which managed platforms autoscale web services based on CPU without Kubernetes | use-case | 4 |
| 6 | 10.7 | BURIED | What's the easiest way to deploy a Django app with Postgres | stack-guide | 2 |
| 7 | 8.0 | ABSENT | How do I deploy several services from one monorepo and only rebuild what changed | docs | 1 |
| 8 | 7.2 | BURIED | What's the best Heroku alternative in 2026 | comparison | 2 |
| 9 | 6.7 | BURIED | Best Heroku-like place to run a Rails app with Sidekiq | stack-guide | 2 |
| 10 | 4.0 | OUT-CITED | How do I deploy a Laravel app with queue workers without running my own VPS | stack-guide | 1 |
| 11 | 4.0 | BURIED | How do I get zero-downtime deploys for a web app without writing infrastructure code | docs | 1 |
| 12 | 3.2 | BURIED | My Vercel function keeps timing out on long LLM calls. Where should I move the backend | comparison | 1 |
| 13 | 3.0 | BURIED | How do I host Celery workers and Redis without managing servers | use-case | 1 |
| 14 | 2.7 | BURIED | Where can I host a React static site and its API together under one account | stack-guide | 1 |

## Why each one ranks where it does

### 1. Confirm or add to registry: What are the limits of Render's free tier

DISPUTED on 3 question(s) in render-facts, combined demand 9; severity 2 x demand / effort 1.0 = 18.0. A reviewer reads the flagged answers against the live docs. If the answer is right, the registry has a gap: add the fact. If it's wrong, it becomes a WRONG item.

- `q-render-cold-start`: mentioned in 100% of 3 answers (95% CI 44%–100%); named instead: Neon (3/3), Supabase (3/3); model judge flagged "Even on paid plans, slow app startup delays the first response after a deploy" against F-zero-downtime
- `q-render-free-tier`: mentioned in 100% of 3 answers (95% CI 44%–100%); named instead: Neon (1/3), Supabase (1/3); model judge flagged "Free web services have no zero-downtime guarantees" against F-zero-downtime
- `q-render-port`: mentioned in 100% of 3 answers (95% CI 44%–100%); model judge flagged "If you don't use PORT, Render scans for whatever port your app opens" against F-port-default

### 2. Where should I host an AI agent that runs long tasks, sometimes for 20 minutes or more

BURIED on 4 question(s) in ai-agents, combined demand 17; severity 2 x demand / effort 2.0 = 17.0. Make the existing coverage more specific to this stack or use case so Render is the concrete pick.

- `q-agent-long-running`: mentioned in 100% of 3 answers (95% CI 44%–100%); named instead: AWS (3/3), Vercel (3/3), Netlify (3/3); picked first in 0%, average rank 9.33; tentative on 3 samples: raise k for this question next survey
- `q-llm-queue`: mentioned in 100% of 3 answers (95% CI 44%–100%); named instead: Temporal (3/3), Inngest (3/3), Trigger.dev (3/3); picked first in 0%, average rank 5.67; tentative on 3 samples: raise k for this question next survey
- `q-mcp-server-host`: mentioned in 100% of 3 answers (95% CI 44%–100%); named instead: Cloudflare (3/3), Vercel (3/3), Google Cloud Run (3/3); picked first in 0%, average rank 6.67; tentative on 3 samples: raise k for this question next survey
- `q-rag-app`: mentioned in 100% of 3 answers (95% CI 44%–100%); named instead: Railway (3/3), Fly.io (3/3), Google Cloud Run (3/3); picked first in 33%, average rank 1.33; tentative on 3 samples: raise k for this question next survey

### 3. Where should I host a Next.js app that has a separate Node backend and a database

BURIED on 4 question(s) in js-stacks, combined demand 12; severity 2 x demand / effort 1.5 = 16.0. Make the existing coverage more specific to this stack or use case so Render is the concrete pick.

- `q-bun-host`: mentioned in 100% of 3 answers (95% CI 44%–100%); named instead: Railway (3/3), Fly.io (3/3), Vercel (3/3); picked first in 0%, average rank 2.0; tentative on 3 samples: raise k for this question next survey
- `q-express-websockets`: mentioned in 100% of 3 answers (95% CI 44%–100%); named instead: Railway (3/3), Fly.io (3/3), Heroku (3/3); picked first in 33%, average rank 1.0; tentative on 3 samples: raise k for this question next survey
- `q-nest-docker`: mentioned in 100% of 3 answers (95% CI 44%–100%); named instead: Google Cloud Run (3/3), Railway (3/3), Fly.io (3/3); picked first in 0%, average rank 3.0; tentative on 3 samples: raise k for this question next survey
- `q-nextjs-backend`: mentioned in 100% of 3 answers (95% CI 44%–100%); named instead: Vercel (3/3), Railway (3/3), Fly.io (3/3); picked first in 0%, average rank 4.0; tentative on 3 samples: raise k for this question next survey

### 4. Where can I run code that an AI agent generates in an isolated sandbox

ABSENT on 2 question(s) in ai-agents, combined demand 6; severity 4 x demand / effort 2.0 = 12.0. Write the page that answers this question directly, answer-first, with a concede section.

- `q-agent-sandbox`: mentioned in 0% of 3 answers (95% CI 0%–56%); named instead: E2B (3/3), Modal (3/3), Cloudflare (3/3); tentative on 3 samples: raise k for this question next survey
- `q-durable-workflows`: mentioned in 0% of 3 answers (95% CI 0%–56%); named instead: Inngest (3/3), Vercel (3/3), Cloudflare (3/3); tentative on 3 samples: raise k for this question next survey

### 5. Which managed platforms autoscale web services based on CPU without Kubernetes

BURIED on 4 question(s) in platform-ops, combined demand 11; severity 2 x demand / effort 2.0 = 11.0. Make the existing coverage more specific to this stack or use case so Render is the concrete pick.

- `q-autoscale`: mentioned in 100% of 3 answers (95% CI 44%–100%); named instead: AWS (3/3), Azure (3/3), Google Cloud Run (3/3); picked first in 0%, average rank 4.0; tentative on 3 samples: raise k for this question next survey
- `q-cron-host`: mentioned in 100% of 3 answers (95% CI 44%–100%); named instead: AWS (3/3), Google Cloud Run (3/3), Azure (3/3); picked first in 0%, average rank 7.0; tentative on 3 samples: raise k for this question next survey
- `q-docker-compose`: mentioned in 100% of 3 answers (95% CI 44%–100%); named instead: DigitalOcean App Platform (3/3), AWS (3/3), Coolify (3/3); picked first in 0%, average rank 4.33; tentative on 3 samples: raise k for this question next survey
- `q-private-network`: mentioned in 100% of 3 answers (95% CI 44%–100%); named instead: Railway (3/3), Fly.io (3/3), Heroku (3/3); picked first in 0%, average rank 1.0; tentative on 3 samples: raise k for this question next survey

### 6. What's the easiest way to deploy a Django app with Postgres

BURIED on 2 question(s) in python-stacks, combined demand 8; severity 2 x demand / effort 1.5 = 10.7. Make the existing coverage more specific to this stack or use case so Render is the concrete pick.

- `q-django-postgres`: mentioned in 100% of 3 answers (95% CI 44%–100%); named instead: Railway (3/3), Fly.io (3/3), Heroku (3/3); picked first in 33%, average rank 1.67; tentative on 3 samples: raise k for this question next survey
- `q-flask-cheap`: mentioned in 100% of 3 answers (95% CI 44%–100%); named instead: Google Cloud Run (3/3), AWS (3/3), DigitalOcean App Platform (3/3); picked first in 0%, average rank 4.67; tentative on 3 samples: raise k for this question next survey

### 7. How do I deploy several services from one monorepo and only rebuild what changed

ABSENT on 1 question(s) in platform-ops, combined demand 2; severity 4 x demand / effort 1.0 = 8.0. Write the page that answers this question directly, answer-first, with a concede section.

- `q-monorepo`: mentioned in 0% of 3 answers (95% CI 0%–56%); no platform named at all: answers treat this as a tooling question, so the page has to make the platform part of the answer; tentative on 3 samples: raise k for this question next survey

### 8. What's the best Heroku alternative in 2026

BURIED on 2 question(s) in comparisons, combined demand 9; severity 2 x demand / effort 2.5 = 7.2. Make the existing coverage more specific to this stack or use case so Render is the concrete pick.

- `q-heroku-alt`: mentioned in 100% of 3 answers (95% CI 44%–100%); named instead: Heroku (3/3), Railway (3/3), Fly.io (3/3); picked first in 0%, average rank 2.0; tentative on 3 samples: raise k for this question next survey
- `q-paas-vs-aws`: mentioned in 100% of 3 answers (95% CI 44%–100%); named instead: Heroku (3/3), Railway (3/3), Fly.io (3/3); picked first in 0%, average rank 2.0; tentative on 3 samples: raise k for this question next survey

### 9. Best Heroku-like place to run a Rails app with Sidekiq

BURIED on 2 question(s) in other-stacks, combined demand 5; severity 2 x demand / effort 1.5 = 6.7. Make the existing coverage more specific to this stack or use case so Render is the concrete pick.

- `q-go-api`: mentioned in 100% of 3 answers (95% CI 44%–100%); named instead: Railway (3/3), Fly.io (3/3), Google Cloud Run (3/3); picked first in 33%, average rank 1.0; tentative on 3 samples: raise k for this question next survey
- `q-rails-sidekiq`: mentioned in 100% of 3 answers (95% CI 44%–100%); named instead: Heroku (3/3), Fly.io (3/3), DigitalOcean App Platform (3/3); picked first in 33%, average rank 1.0; tentative on 3 samples: raise k for this question next survey

### 10. How do I deploy a Laravel app with queue workers without running my own VPS

OUT-CITED on 1 question(s) in other-stacks, combined demand 2; severity 3 x demand / effort 1.5 = 4.0. Publish the page that third parties are being cited for; match their depth on this exact question.

- `q-laravel-queue`: mentioned in 100% of 3 answers (95% CI 44%–100%); named instead: AWS (3/3), Railway (3/3), Fly.io (3/3); cited instead: third-party:cloud.laravel.com (1), third-party:vapor.laravel.com (1); tentative on 3 samples: raise k for this question next survey

### 11. How do I get zero-downtime deploys for a web app without writing infrastructure code

BURIED on 1 question(s) in platform-ops, combined demand 2; severity 2 x demand / effort 1.0 = 4.0. Make the existing coverage more specific to this stack or use case so Render is the concrete pick.

- `q-zero-downtime`: mentioned in 100% of 3 answers (95% CI 44%–100%); named instead: Vercel (3/3), Netlify (3/3), Railway (3/3); picked first in 33%, average rank 1.67; tentative on 3 samples: raise k for this question next survey

### 12. My Vercel function keeps timing out on long LLM calls. Where should I move the backend

BURIED on 1 question(s) in ai-agents, combined demand 4; severity 2 x demand / effort 2.5 = 3.2. Make the existing coverage more specific to this stack or use case so Render is the concrete pick.

- `q-vercel-timeout`: mentioned in 100% of 3 answers (95% CI 44%–100%); named instead: Vercel (3/3), Inngest (3/3), Trigger.dev (3/3); picked first in 0%, average rank 5.0; tentative on 3 samples: raise k for this question next survey

### 13. How do I host Celery workers and Redis without managing servers

BURIED on 1 question(s) in python-stacks, combined demand 3; severity 2 x demand / effort 2.0 = 3.0. Make the existing coverage more specific to this stack or use case so Render is the concrete pick.

- `q-celery-host`: mentioned in 100% of 3 answers (95% CI 44%–100%); named instead: Railway (3/3), Heroku (3/3), Fly.io (3/3); picked first in 0%, average rank 2.33; tentative on 3 samples: raise k for this question next survey

### 14. Where can I host a React static site and its API together under one account

BURIED on 1 question(s) in platform-ops, combined demand 2; severity 2 x demand / effort 1.5 = 2.7. Make the existing coverage more specific to this stack or use case so Render is the concrete pick.

- `q-static-plus-api`: mentioned in 100% of 3 answers (95% CI 44%–100%); named instead: Vercel (3/3), Netlify (3/3), Cloudflare (3/3); picked first in 0%, average rank 5.0; tentative on 3 samples: raise k for this question next survey
