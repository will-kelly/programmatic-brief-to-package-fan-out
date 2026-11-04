---
title: What Render's free tier covers
format: docs
target_questions: [q-render-free-tier]
last_verified: 2026-11-04
expect_flagged:
expect_lint:
---

# What Render's free tier covers

Use the free tier for prototypes and demos, not for anything that has to answer the first request fast. A free web service spins down after 15 minutes without inbound traffic. [C1]

## What happens on the first request after a spin-down?

The request waits while Render spins the service back up, which can take up to a minute. [C2]

## Can I run a worker or a cron job for free?

No. Background workers and cron jobs aren't available on the free instance type. [C3]

## Does free Postgres last?

A free Render Postgres database expires 30 days after it's created. [C4]

## When Render isn't the right fit

If a demo has to respond instantly to its first visitor, pay for an always-on instance or pick a host whose free tier doesn't sleep.

<!-- claims
C1 | A free web service spins down after 15 minutes without inbound traffic. | free#spin-down
C2 | The first request after a spin-down waits while the service spins up, which can take up to a minute. | free#spin-down
C3 | Background workers and cron jobs aren't available on the free instance type. | free#unsupported
C4 | A free Render Postgres database expires 30 days after it's created. | free#postgres
-->
