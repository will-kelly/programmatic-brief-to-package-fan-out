# One run, start to finish

Everything here came from one session on 2026-11-04. Model output is
unedited. Docs, signals, and the partner draft are synthetic (see the main
README). Total model spend was $9.10.

## 1. Survey: `survey-2026-11-04-claude/`

36 questions × 3 samples, asked of Claude with no web search. Start with
`summary.md`. `answers.jsonl` has every answer with its scoring: mentions,
rank, first pick, citations, and judged claims. You can rescore it without
new calls:

```bash
./cf survey --resummarize examples/survey-2026-11-04-claude --rescore
```

That rescore path earned its keep. The first pass counted URLs from code
samples (`localhost`, `example.com`, `{h}`) as citations and diagnosed 6
questions as OUT-CITED. After stripping code and placeholder hosts, 1 was
left, and the rest moved to BURIED, which matches a model answering from
memory.

## 2. Backlog: `backlog.md`

14 items, ranked. The top one is DISPUTED: verify three model-flagged
"wrong" answers before acting on them. My read is that all three are
registry gaps. For example, Claude said Render scans for an open port if
you don't bind to `PORT`, and the seed registry doesn't cover that
behavior. Measurement gets fixed before content.

## 3. Brief: `brief-agent-long-running.md`

The ai-agents BURIED item, as a brief that works for in-house or partner
writers. I issued it before the citation fix, so it lists 3 questions. The
current backlog groups a 4th (remote MCP servers) into the same item.

## 4. Two drafts: `run-1-section-retrieval/`, `run-2-page-retrieval/`

The same brief drafted twice, with one change to the research stage between
runs.

| | Run 1 | Run 2 |
|---|---|---|
| Research | top sections by term overlap | whole pages for every section hit |
| Sections in the source pack | 10 | 16 |
| Claims, all tied to a docs section | 18 | 21 |
| Open TKs | 14 | 11 |
| Contradicted claims | 0 | 0 |
| Estimated review time | 13.0 min | 14.5 min |

The docs-gap report found the bug. Run 1 left a TK on "whether background
workers have a free instance type," but the fixture answers that in
`free#unsupported`, a section the research stage never retrieved. Both runs
are blocked on purpose: open TKs block publishing, and the remaining 11 are
facts the thin fixture doesn't state (request timeouts, worker shutdown
grace period, pgvector support). `docs-gaps.md` lists them for the docs
owners.

## 5. Partner check: `partner-check/`

`fixtures/partner/heroku-alternatives-draft.md` is a partner-style draft
with no claims ledger, so the checker extracted one. It's blocked on:

- the claim that Render's free tier includes background workers, caught by
  a known-wrong pattern
- "robust"
- an opener that's preamble, not an answer
- a comparison with no section on when another option wins

The packet is what the partner gets back.

## 6. Refresh: `refresh-simulated/`

I published the clean free-tier page from `evals/cases/`, then changed one
sentence in the docs (`free.v2.md`: spin-down 15 → 20 minutes, a simulated
change). The refresh flagged the 2 claims citing `free#spin-down`, marked
the 15-minute claim as broken on the figure mismatch alone, and confirmed
the other still holds. The page's other 2 claims weren't touched.

## 7. Evals: `eval-claude-judge.txt`, `eval-fake-judge.txt`

The same cases with planted errors under both judges. The keyword fake
misses "A background worker can run on the free instance type," a claim
whose words all appear in the evidence but whose meaning doesn't. The
Claude judge catches it.

## 8. Scorecard: `scorecard.md`

Visibility with intervals, firm and disputed accuracy, registry coverage,
review time, freshness, spend by stage, and partners. Auto-verified reads
0% because the evidence is a fixture, not live docs, and the scorecard says
so instead of rounding up.
