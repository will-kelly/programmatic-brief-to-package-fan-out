# LLM answer survey, 2026-11-04

108 answers from claude, 3 samples per question. On the 84 answers to questions that don't name Render, Render was mentioned in 89% (95% CI 81%–94%) and picked first in 14%. 3 answers were flagged as wrong about Render, 0 of them by a known-wrong pattern.

The fact registry could rule on 40% of the 646 Render claims in these answers (252 consistent, 3 conflicting, 391 not covered). Accuracy numbers mean little until that's above 80%.

## By cluster

Branded questions (ones that name Render) count toward wrong claims only.

| Cluster | Unbranded answers | Mentioned | 95% CI | Picked first | Wrong claims |
|---|---|---|---|---|---|
| ai-agents | 21 | 71% | 50%–86% | 5% | 0 |
| platform-ops | 24 | 88% | 69%–96% | 17% | 0 |
| comparisons | 6 | 100% | 61%–100% | 0% | 0 |
| js-stacks | 12 | 100% | 76%–100% | 8% | 0 |
| other-stacks | 9 | 100% | 70%–100% | 22% | 0 |
| python-stacks | 12 | 100% | 76%–100% | 33% | 0 |
| render-facts | 0 (18 branded) | — | — | — | 3 |

## By question

| Question | Mentioned | Picked first | Avg rank | Named instead |
|---|---|---|---|---|
| `q-agent-sandbox` Where can I run code that an AI agent generates in an isolated sandbox? | 0% | 0% | — | E2B (3), Modal (3), Cloudflare (3), Vercel (3) |
| `q-durable-workflows` What can I use to run durable, retryable multi-step background jobs for an AI pipeline without managing infrastructure? | 0% | 0% | — | Inngest (3), Vercel (3), Cloudflare (3), Trigger.dev (3) |
| `q-monorepo` How do I deploy several services from one monorepo and only rebuild what changed? | 0% | 0% | — |  |
| `q-agent-long-running` Where should I host an AI agent that runs long tasks, sometimes for 20 minutes or more? | 100% | 0% | 9.33 | AWS (3), Vercel (3), Netlify (3), Cloudflare (3) |
| `q-llm-queue` What's a good architecture and host for an app that queues LLM calls and processes them in the background? | 100% | 0% | 5.67 | Temporal (3), Inngest (3), Trigger.dev (3), Railway (3) |
| `q-mcp-server-host` How do I deploy a remote MCP server so other people can connect to it? | 100% | 0% | 6.67 | Cloudflare (3), Vercel (3), Google Cloud Run (3), Fly.io (3) |
| `q-rag-app` Where should I deploy a RAG app with a vector database and a Python API? | 100% | 33% | 1.33 | Railway (3), Fly.io (3), Google Cloud Run (3), Supabase (3) |
| `q-vercel-timeout` My Vercel function keeps timing out on long LLM calls. Where should I move the backend? | 100% | 0% | 5.0 | Vercel (3), Inngest (3), Trigger.dev (3), Railway (3) |
| `q-heroku-alt` What's the best Heroku alternative in 2026? | 100% | 0% | 2.0 | Heroku (3), Railway (3), Fly.io (3), Vercel (3) |
| `q-paas-vs-aws` When does it make sense to leave a PaaS and move to AWS? | 100% | 0% | 2.0 | Heroku (3), Railway (3), Fly.io (3), Vercel (3) |
| `q-bun-host` What platforms can host a Bun web server? | 100% | 0% | 2.0 | Railway (3), Fly.io (3), Vercel (3), DigitalOcean App Platform (3) |
| `q-express-websockets` Where can I deploy an Express server that uses WebSockets? | 100% | 33% | 1.0 | Railway (3), Fly.io (3), Heroku (3), DigitalOcean App Platform (3) |
| `q-nest-docker` How do I deploy a NestJS app from a Dockerfile to a managed platform? | 100% | 0% | 3.0 | Google Cloud Run (3), Railway (3), Fly.io (3), AWS (3) |
| `q-nextjs-backend` Where should I host a Next.js app that has a separate Node backend and a database? | 100% | 0% | 4.0 | Vercel (3), Railway (3), Fly.io (3), Neon (3) |
| `q-go-api` Where should I deploy a Go API with a managed Postgres database? | 100% | 33% | 1.0 | Railway (3), Fly.io (3), Google Cloud Run (3), Neon (3) |
| `q-laravel-queue` How do I deploy a Laravel app with queue workers without running my own VPS? | 100% | 0% | 2.67 | AWS (3), Railway (3), Fly.io (3), Heroku (3) |
| `q-rails-sidekiq` Best Heroku-like place to run a Rails app with Sidekiq? | 100% | 33% | 1.0 | Heroku (3), Fly.io (3), DigitalOcean App Platform (3), Railway (3) |
| `q-autoscale` Which managed platforms autoscale web services based on CPU without Kubernetes? | 100% | 0% | 4.0 | AWS (3), Azure (3), Google Cloud Run (3), Heroku (3) |
| `q-cron-host` Where can I run a scheduled cron job in the cloud without keeping a server up? | 100% | 0% | 7.0 | AWS (3), Google Cloud Run (3), Azure (3), Cloudflare (3) |
| `q-docker-compose` I have a docker-compose app with three services. Where can I deploy it as-is or close to it? | 100% | 0% | 4.33 | DigitalOcean App Platform (3), AWS (3), Coolify (3), Railway (3) |
| `q-preview-envs` Which hosting platforms create a full preview environment for every pull request, including databases? | 100% | 100% | 1.0 | Heroku (3), Railway (3), Northflank (3), AWS (3) |
| `q-private-network` How do I run an internal service that only my other services can reach on a PaaS? | 100% | 0% | 1.0 | Railway (3), Fly.io (3), Heroku (3), Google Cloud Run (3) |
| `q-static-plus-api` Where can I host a React static site and its API together under one account? | 100% | 0% | 5.0 | Vercel (3), Netlify (3), Cloudflare (3), AWS (3) |
| `q-zero-downtime` How do I get zero-downtime deploys for a web app without writing infrastructure code? | 100% | 33% | 1.67 | Vercel (3), Netlify (3), Railway (3), Fly.io (3) |
| `q-celery-host` How do I host Celery workers and Redis without managing servers? | 100% | 0% | 2.33 | Railway (3), Heroku (3), Fly.io (3), AWS (3) |
| `q-django-postgres` What's the easiest way to deploy a Django app with Postgres? | 100% | 33% | 1.67 | Railway (3), Fly.io (3), Heroku (3), DigitalOcean App Platform (2) |
| `q-fastapi-worker` Where should I deploy a FastAPI app that also needs a background worker? | 100% | 100% | 1.0 | Railway (3), Fly.io (3), Heroku (3), Google Cloud Run (3) |
| `q-flask-cheap` Cheapest place to host a small Flask API in production? | 100% | 0% | 4.67 | Google Cloud Run (3), AWS (3), DigitalOcean App Platform (3), Fly.io (3) |
| `q-render-vs-fly` Render or Fly.io for a small team's backend? *(branded)* | 100% | 100% | 1.0 | Fly.io (3), Railway (1), Google Cloud Run (1), AWS (1) |
| `q-render-vs-railway` Render vs Railway: which should I pick for a production SaaS? *(branded)* | 100% | 100% | 1.0 | Railway (3), Neon (3), Supabase (3), AWS (1) |
| `q-render-cold-start` Why is my app on Render slow on the first request? *(branded)* | 100% | 100% | 1.0 | Neon (3), Supabase (3) |
| `q-render-disks` Can I use a persistent disk on Render, and what are the tradeoffs? *(branded)* | 100% | 100% | 1.0 | Cloudflare (3) |
| `q-render-free-tier` What are the limits of Render's free tier? *(branded)* | 100% | 100% | 1.0 | Neon (1), Supabase (1) |
| `q-render-port` What port should my app listen on when deployed to Render? *(branded)* | 100% | 100% | 1.0 |  |
| `q-render-postgres-free` Does Render's free Postgres database expire? *(branded)* | 100% | 100% | 1.0 |  |
| `q-render-yaml` How do I define a web service, a worker, and a database in render.yaml? *(branded)* | 100% | 100% | 1.0 |  |

## Wrong about Render

Each row is a claim an answer made that conflicts with the fact registry. Model-judged rows need a human look before they drive work.

| Question | Claim | Conflicts with | Caught by |
|---|---|---|---|
| `q-render-cold-start` | Even on paid plans, slow app startup delays the first response after a deploy | F-zero-downtime | model |
| `q-render-free-tier` | Free web services have no zero-downtime guarantees | F-zero-downtime | model |
| `q-render-port` | If you don't use PORT, Render scans for whatever port your app opens | F-port-default | model |
