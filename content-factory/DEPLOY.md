# Deploying the factory

Two paths. Do the first before the second.

## 1. Run it against real data from your laptop

Nothing here needs Render's cooperation. Everything reads public docs and
asks public models.

**Snapshot the real docs.** If Render publishes an `llms-full.txt`, point the
snapshot at the URL. Otherwise save the docs pages the question set touches
as Markdown in a folder and point it there.

```bash
./cf docs snapshot --from https://render.com/docs/llms-full.txt
```

Claims supported by this snapshot come back VERIFIED instead of
CORROBORATED.

**Grow the fact registry** in `config/facts.toml`. Start with the three
DISPUTED claims in `examples/backlog.md`, then the most common uncovered
claims in the survey answers. Each fact needs a `source` that exists in the
snapshot; `./cf refresh` lists facts whose source section is missing.

**Rerun the loop** with the API backend or the `claude` CLI:

```bash
export CF_LLM=anthropic ANTHROPIC_API_KEY=...
```

```bash
./cf survey -k 5
```

```bash
./cf gaps && ./cf metrics --targets ai-agents
```

Add a search-enabled engine for real citations by exporting its answers as
JSONL (`question_id`, `engine`, `answer`, `cited_urls`):

```bash
./cf survey --engine import:perplexity-answers.jsonl
```

## 2. Run it on Render Workflows

### What's already handled

- **Model calls:** `CF_LLM=anthropic` calls the Messages API with
  `claude-opus-5-5`, adaptive thinking, an effort level per role, prompt
  caching on the fixed system prompts, and server-side refusal fallback.
  The cost of every call is logged to `llm-calls.jsonl` from the usage block.
- **State across fresh compute:** with `CF_STATE_URL` set, every task pulls
  state from Postgres on start and pushes on exit, including on failure.
  Append-only logs merge row by row, so the parallel survey tasks don't
  overwrite each other. `tests/test_deploy.py` runs the whole weekly cycle
  with the disk wiped before every task and checks that nothing is lost. It
  passes against SQLite and against Postgres 16.
- **Survey fan-out:** one task per topic cluster, merged into one survey
  before gap analysis.

### Steps

1. **Verify the SDK.** Install the `render_sdk` version you'll pin and check
   the `VERIFY` notes in `workflows/render_workflows.py` against Render's
   Python SDK reference: the import path, whether awaiting a task from a
   task runs it as a subtask, and which return types a task allows. Pin the
   version in `requirements.txt`.
2. **Create a Render Postgres database.** Copy its internal connection
   string for `CF_STATE_URL`. The factory creates its two tables
   (`cf_files`, `cf_lines`) on first use.
3. **Create the Workflows service** from this repo, with
   `content-factory/` as the root directory. Install with
   `pip install -r requirements.txt` and start with
   `python workflows/render_workflows.py`. Take the service type and any
   Blueprint fields from Render's Workflows setup docs; I didn't write a
   `render.yaml` because I couldn't confirm those fields.
4. **Set environment variables:**

   | Variable | Value |
   |---|---|
   | `CF_LLM` | `anthropic` |
   | `ANTHROPIC_API_KEY` | secret |
   | `CF_STATE_URL` | the Postgres internal URL |
   | `CF_DOCS_SRC` | docs URL or path (defaults to `https://render.com/docs/llms-full.txt`) |
   | `CF_TRAFFIC_LOG` | optional, path to an agent access log |
   | `PYTHONPATH` | the content-factory root, so `factory` imports |

5. **Seed the database** from your laptop with the state from part 1, so
   the first cloud run starts from your catalog and registry work:

   ```bash
   CF_STATE_URL=postgresql://... ./cf state push
   ```

6. **Schedule `weekly_cycle`** and trigger `produce` with a brief path,
   either on demand or for the top backlog items. `produce` stops at the
   review packet.
7. **Review from anywhere:** pull state, read the packets, record reviews,
   publish, push.

   ```bash
   ./cf state pull
   ```

   ```bash
   ./cf review done state/runs/<piece>/<run> --minutes 12 --corrections 1
   ```

   ```bash
   ./cf publish state/runs/<piece>/<run> && ./cf state push
   ```

### Cost

At list prices for Claude Opus 5.5, the weekly survey with judging costs
about $8 at `-k 3` and $13 at `-k 5`; each drafted and checked piece costs
about $1.50. The judge is the biggest line item: run the judge-agreement
eval before moving it to a cheaper model (`CF_MODEL` is global; split it per
role in `factory/llm.py` if the eval says a cheaper judge holds).

### Not handled yet

- Locking around `publish` and `refresh`. Both write `catalog.json`; run
  them from one place.
- Large files in Postgres. Docs snapshots are a few MB at most, so this
  doesn't matter until you store page HTML.
- Signup attribution. The scorecard leaves it blank until there's a real
  join between page views and signup source.
