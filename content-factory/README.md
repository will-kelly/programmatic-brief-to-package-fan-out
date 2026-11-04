# Render content factory

A working build of the system in Render's Senior Content Engineer posting:
measure where Render shows up in LLM answers, diagnose why it doesn't, rank
the fixes, then research, draft, fact-check, and refresh the content that
closes the gaps. It runs locally with `./cf` and maps onto Render Workflows
tasks (`workflows/`).

I built it the way I'd run the job. That means the factory spends as much
effort deciding what not to write as it does writing.

## What the first survey found

I asked Claude 36 developer questions, 3 times each, with no web search. That
measures what the model already knows, which is what training-crawler traffic
feeds. The run cost $7.65. Full output is in
[`examples/survey-2026-11-04-claude/`](examples/survey-2026-11-04-claude/summary.md).

- **Render is on the list, not the pick.** It was mentioned in 89% of answers
  to questions that don't name it (95% CI 81–94%), but picked first in 14%.
  The main gap is being the default, not being visible. Volume alone won't
  fix that. Specificity will.
- **Agent workloads are the weak cluster.** That's the cluster that matters
  most for an AI-native cloud. AI agent questions got a 71% mention rate and
  a 5% first-pick rate. On "host an agent that runs 20+ minute tasks," Render
  came up at an average rank of 9.3.
- **Claude doesn't connect Render to durable workflows.** Asked how to run
  durable, retryable multi-step jobs for an AI pipeline, Claude named
  Inngest, Trigger.dev, and Temporal in all 3 answers and Render in none.
  That's the category Render Workflows sells into. Three samples can't rule
  out a 56% mention rate, so the backlog marks it tentative and the next
  survey samples it harder.
- **The accuracy number isn't trustworthy yet, and the factory says so.**
  The model judge flagged 3 answers as wrong about Render. On a read, all 3
  look like gaps in my 14-fact seed registry, not model errors. The registry
  could rule on only 40% of the 646 Render claims in the answers. Until that
  passes 80%, "LLMs are accurate about Render" isn't a claim this survey can
  make. So the top backlog item is fixing the measurement, not a piece of
  content.

## Where this departs from a standard content factory

**Diagnose before you write.** Each question gets one of six diagnoses, and
each one has a different fix:

| Diagnosis | What the signals show | Fix |
|---|---|---|
| WRONG | An answer states something false, caught by a known-wrong pattern or a human | Correct the docs and the registry first, then the pages that repeat it |
| DISPUTED | Only the model judge says it's wrong | A human confirms. Nobody ships a correction on a model's say-so |
| ABSENT | Render is missing and competitors are named | A new page, answer-first |
| BURIED | Render is named but late, or rarely the pick | A narrower, more specific page |
| OUT-CITED | Someone else's URL is the source | A page worth citing on exactly that question |
| UNRETRIEVED | We have a page, but index and live-fetch agents never reach it | Discoverability work (llms.txt, markdown twins, links). Writing more won't help |

The backlog ranks by severity × demand ÷ effort, and every row carries its
evidence. Wrong answers rank above missing ones because they get repeated
and trained on.

**Review claims, not prose.** Every draft carries a claims ledger: each claim,
tagged in the copy, tied to a docs section. The checker runs the cheap
checks first: known-wrong patterns, whether the cited section exists, and
whether the numbers match. Only then does a model judge see the claim. Each
claim ends up in one of three tiers:

- VERIFIED: supported by the live docs.
- CORROBORATED: supported only by the fixture or a seed fact.
- SIGNAL: a human has to decide.

The expert's review packet leads with the SIGNAL claims, with the docs text
printed next to each one. On the agent-hosting draft, that's an estimated 15
minutes of review instead of about 50. Those estimates come from the time
model in `pipeline.py` until reviewers log real minutes.

**Staleness belongs to claims, not pages.** Publishing records the hash of
every docs section each claim cites. When a docs snapshot changes one
section, the refresh job flags the claims that cite it and rechecks them.
It doesn't flag every page older than 90 days. In the simulated run, a
spin-down change from 15 to 20 minutes flagged 2 of the page's 4 claims and
broke 1 ([`examples/refresh-simulated/`](examples/refresh-simulated/refresh-queue.md)).

**A TK is a docs ticket.** Writers leave `[[TK: ...]]` instead of guessing.
`cf docs gaps` rolls every open TK across drafts into a list for the docs
owners, ranked by how many pieces are blocked on the same missing fact. It
also flags TKs the docs already answer but the research stage didn't
retrieve. That's how I caught a retrieval bug: the fix cut one draft from
14 TKs to 11.

**Concede, or read as an ad.** Comparisons fail the linter unless they include
a section on when the other option wins. Use-case pages get a warning
without one. One-sided pages read as vendor copy, to developers and to
whatever ranks sources.

**One bar for partners and in-house drafts.** A partner runs `cf check` on a
draft before sending it and gets the same verdicts and packet the internal
pipeline produces. The scorecard tracks each partner's first-check pass
rate, contradictions per draft, and lint errors per draft. The sample partner
draft was blocked for claiming the free tier includes background workers,
plus a "robust" and a one-sided comparison.

**Reviewer misses become evals.** `cf review done --escaped C3` turns a claim
the checker passed and a human caught into a test case. `cf eval` scores
the checker against planted errors before any prompt, pattern, or model
change ships. Baselines are kept per judge mode. The real Claude judge
catches a negation the keyword fake can't (recall 1.0 vs 0.75), and that gap
is the reason the model judge exists.

**Intervals, not anecdotes.** Answers are sampled, so every rate carries a
Wilson interval. Questions that name Render get scored for accuracy only,
since naming Render always gets Render back. The scorecard leads with
visibility and accuracy, and it leaves attributed signups blank until a
real join exists.

## How it maps to the role

| The posting says | Here |
|---|---|
| Content gap analysis from AEO benchmarks, citation tracking, agent traffic | `cf survey`, `cf gaps --traffic access.log --citations export.csv` |
| A prioritized backlog with clear reasoning | `state/backlog.md`: score, diagnosis, and evidence per row |
| AI-assisted pipelines on Render Workflows that research, draft, fact-check | `cf run BRIEF`, `workflows/render_workflows.py` |
| Test changes with evals | `cf eval`, per-mode baselines, fails on regression |
| Make expert review faster and cheaper, track accuracy | Claim tiers, review packets, `cf review done`, scorecard |
| Refresh cycle as the product changes | `cf docs snapshot`, `cf refresh` |
| Briefs, feedback, and quality for external partners | `cf brief N`, `cf check --partner NAME`, partner table |
| Expand docs coverage where it drives citations | `cf docs gaps` |
| Metrics beyond volume | `cf metrics` |
| Automated fact-check against live Render docs | `factory/factcheck.py` over a docs snapshot |
| Recurring survey of LLM answers | `cf survey`, weekly in `weekly_cycle` |

## Pipeline

```
config/questions.toml ──► survey ──► answers.jsonl, summary (rates + intervals)
                                        │
agent access log ──► signals ───────────┤
citation export ────────────────────────┤
catalog.json (published claims) ────────┤
                                        ▼
                              gaps ──► backlog.md (diagnosis, score, evidence)
                                        │
                              brief N ──► brief.md (same file for partners)
                                        │
docs snapshot ──► research ──► draft ──► check ──► review-packet.md
 (section hashes)  (source pack)  (ledger)  │  patterns → source → figures → model judge
                                            ▼
                                   human review ──► publish ──► catalog.json
                                            │                       │
                         escaped errors ──► evals/cases/     docs change
                                                                    ▼
                                                     refresh ──► refresh-queue.md
```

## Run it

Python 3.11+, standard library only. Model calls go through the `claude` CLI
headless, with tools off. Set `CF_LLM=fake` to run everything offline.

```bash
./cf docs snapshot --from fixtures/docs
```

```bash
./cf survey -k 3
```

```bash
./cf gaps --traffic fixtures/signals/access.log --citations fixtures/signals/citations.csv
```

```bash
./cf brief 2
```

```bash
./cf run state/briefs/<brief>.md
```

```bash
./cf check partner-draft.md --brief state/briefs/<brief>.md --partner acme
```

```bash
./cf refresh
```

```bash
./cf eval
```

```bash
./cf metrics --targets ai-agents
```

Tests run the whole loop offline:

```bash
python3 tests/test_factory.py
```

## What's real and what isn't

- **Real:** the survey (108 Claude answers), both drafts, the model-judged
  fact-checks, the partner check, and the Claude-judge eval run. Total model
  spend for everything in `examples/` was $9.10.
- **Synthetic:** `fixtures/docs/` is a stand-in for Render's docs, written
  from memory because render.com was unreachable from the build
  environment. It's why every supported claim lands as CORROBORATED, never
  VERIFIED. `config/facts.toml` is a 14-fact seed. The access log and
  citation export in `fixtures/signals/` are invented shapes for the demo.
  The partner draft is one I wrote with planted faults. The refresh run
  uses a simulated docs change, not a real one.
- **Unverified:** `workflows/render_workflows.py` follows the documented
  Workflows pattern (`Workflows()`, `@app.task(timeout_seconds=...)`,
  `app.start()`). It marks three SDK details to check against the version
  you pin.

## What I'd do next at Render

1. Point `cf docs snapshot` at the real docs, and grow the registry from the
   391 uncovered claims in the survey until coverage passes 80%.
2. Add search-enabled engines (Perplexity, ChatGPT search, AI Overviews)
   through `--engine import:`. Citations only mean something with
   retrieval, and the OUT-CITED diagnosis needs them.
3. Raise k to 10 on the tentative questions, starting with durable
   workflows and agent sandboxes.
4. Run the judge-agreement eval: a cheaper model against the current judge
   on the same claims. Survey judging cost more than the answers did
   ($4.05 vs $3.60).
5. Join real agent traffic from the docs CDN logs to the catalog, so
   UNRETRIEVED stops being a hypothesis.

## Layout

```
cf                         CLI entry
config/                    questions, brands, fact registry, voice
prompts/draft.md           drafting contract (answer-first, claim tags, concede)
factory/                   survey, brands, signals, gaps, briefs, docs,
                           pipeline, factcheck, lint, refresh, evals, metrics
workflows/                 Render Workflows task bindings
evals/                     cases with planted errors, per-mode baselines
fixtures/                  synthetic docs, signals, partner draft
examples/                  one real end-to-end run (see examples/README.md)
tests/test_factory.py      offline end-to-end tests
```
