# Brief-to-package fan-out

Drop a research brief in a folder and run one command. Five Claude Code agents
write in parallel, each in its own directory:

| Agent | Writes | Output |
|---|---|---|
| `longform` | The anchor piece, 1,800 to 2,500 words | `article.md` |
| `linkedin` | A 3 to 5 post series plus a posting plan | `post-01.md` … `series-plan.md` |
| `newsletter` | One edition with subject lines and preview text | `edition.md` |
| `proof-points` | ADD, UPDATE, and RETIRE entries for your proof-point bank | `proof-points.md` |
| `talk` | A 20-minute slide outline with speaker notes | `outline.md` |

Then a reconciliation editor reads all five and fixes contradictions, factual
drift from the brief, and the same anecdote turning up in several channels.
Each run is a directory of plain files, so you can diff it against the last
one.

```
./fanout
```

## A real run

`examples/sample-run/` is one unedited run on `examples/ai-pilot-stall.md`
(a brief with invented figures). It took 6.6 minutes and cost $2.63. The
writers ran in parallel, the slowest taking 2.3 minutes, and the editor took
4.3 minutes. The precheck found three anecdotes reused across channels (one
of them in four places) and a "day 45" figure the newsletter made up. The
editor gave each anecdote one home and removed the invented figure. It also
fixed a contradiction the script couldn't see: the talk said to set the
success measure after two weeks, while every other channel said week one.
Start with `reconciliation/report.md` and `reconciliation/editor.diff`.

The writers' main habit is reaching for the same strongest story, so most of
the editor's time goes on reallocating anecdotes. Give the brief more
anecdotes than channels and the editor has spare ones to swap in.

## How a run works

```
briefs/inbox/my-brief.md
        │
        ▼
  runs/<slug>/<run-id>/brief.md   (copied, read-only)
        │
        ├── longform ─────┐
        ├── linkedin ─────┤   parallel; each can write only to
        ├── newsletter ───┤   drafts/<channel>/
        ├── proof-points ─┤
        └── talk ─────────┘
                │
                ▼
     lib/ledger.py check          mechanical precheck: anecdote reuse,
     → reconciliation/precheck.md  figures not in the brief, unknown IDs, length
                │
                ▼
     editor (copies drafts → final/, edits final/ in place)
     → reconciliation/report.md
                │
                ▼
     lib/ledger.py check --strict  postcheck; unresolved errors fail the run
     → reconciliation/postcheck.md
     → reconciliation/editor.diff     what the editor changed
     → reconciliation/vs-previous.diff what changed since the last run
     → manifest.json                  status, cost, timing, input hashes
```

Every agent is a headless `claude -p` call running in the run directory, with
only the `Read`, `Write`, `Edit`, `Glob`, and `Grep` tools and write
permission scoped to its own directory (`Edit(./drafts/linkedin/**)` and so
on, in `dontAsk` mode). A writer can't touch another writer's files or the
brief, and the editor can write only to `final/` and `reconciliation/`. The
untouched drafts stay in `drafts/`, so `editor.diff` shows every change the
editor made.

### The ledger is what makes reconciliation checkable

Each writer also writes `ledger.json`: the thesis as that channel states it,
every anecdote ID it used, and every evidence ID with the exact figures
quoted. `lib/ledger.py` reads the ledgers and the brief and reports, without
a model:

- **Anecdote reuse:** an anecdote ID in more than one writer channel, unless
  the brief marks it `(shared)`. The proof-point bank is exempt.
- **Figure drift:** a figure attributed to `[E3]` that doesn't appear in the
  brief at all is an error. One that appears in the brief, but not in E3's
  entry, is a warning.
- **Possible invention:** anecdote or evidence IDs that aren't in the brief.
- **Untraced figures:** percentages, money, and numbers 11 or over in the copy
  that aren't anywhere in the brief (a warning, since the check is a
  heuristic).
- **Format:** LinkedIn posts over 3,000 characters, files missing from or
  missing in the ledger, open `[[TK: ...]]` placeholders.

The editor starts from that report and then looks for what the script can't
see: claims that contradict each other in meaning, recommendations that
diverge, repeated hook lines. After the editor finishes, the same check runs
again with `--strict`. If errors remain, the run is marked `needs-review` and
`fanout` exits non-zero, with the leftover issues printed.

## Requirements

- Claude Code (`claude`), logged in or with `ANTHROPIC_API_KEY` set.
- Bash 4.3 or later. On macOS, `brew install bash` (the system bash is 3.2).
- Python 3.8 or later, standard library only.
- `timeout` (GNU coreutils) is used if present; on macOS, `brew install
  coreutils` gives `gtimeout`, which also works.

## Writing a brief

Copy `examples/ai-pilot-stall.md`. Its format is what the agents and the
checker expect:

- Optional front matter with `slug:`. Without it, the slug is the filename.
- Tag each piece of evidence `[E1]`, `[E2]`, … and each anecdote `[A1]`,
  `[A2]`, …. An ID's entry is its line plus the lines after it, up to a blank
  line or the next ID. Figures cited against an ID are checked against that
  entry.
- Mark an anecdote `(shared)` on its line if it's allowed in more than one
  channel, such as your own signature story.
- Give the package enough anecdotes to go around. With five channels and one
  story, the editor can only remove it from four places and leave TKs.

The writers are told to use only what's in the brief and to leave
`[[TK: what's missing]]` rather than fill a gap.

## Commands

```bash
./fanout
```

Runs every brief in `briefs/inbox/` that is new or changed since its last
successful run. Unchanged briefs are skipped.

```bash
./fanout run path/to/brief.md --force
```

Runs one brief. `--force` reruns it even if it hasn't changed, which is how
you rerun after editing an agent prompt or the voice file.

```bash
./fanout watch 10
```

Polls the inbox every 10 seconds, so dropping a file into the folder starts a
run.

```bash
./fanout diff ai-pilot-stall
```

Diffs the final output of the two most recent runs for that slug. Pass two run
IDs to compare specific runs.

```bash
./fanout list
```

Lists every run with its outcome, wall-clock time, and cost.

## Run directory

```
runs/ai-pilot-stall/
├── latest -> 20261031T183045Z
├── .brief-sha                    hash of the last brief that ran cleanly
└── 20261031T183045Z/
    ├── brief.md  voice.md  [bank.md]
    ├── prompts/<agent>.md        the exact system prompt each agent got
    ├── drafts/<channel>/         writer output, read-only after the fan-out
    ├── final/<channel>/          reconciled output: this is the package
    ├── reconciliation/
    │   ├── precheck.md|json
    │   ├── report.md             the editor's change table and allocation
    │   ├── postcheck.md|json
    │   ├── editor.diff
    │   └── vs-previous.diff
    ├── logs/<agent>.json|err     claude's result JSON: cost, turns, duration
    └── manifest.json
```

`manifest.json` records the sha256 of the brief, voice file, bank, and every
agent prompt, so when two runs differ you can tell whether the inputs changed
or only the model's output did. Commit `runs/` if you want the history in git;
nothing in it is ignored by default.

## Configuration

- **Voice:** `config/voice.md` is read by every agent. Replace it with your own
  locked voice config.
- **Proof-point bank:** put your current bank at `config/proof-point-bank.md`
  and the proof-points agent updates it instead of starting fresh.
- **Agents:** each one is a Markdown file in `agents/`. `_contract.md` is
  prepended to every writer (sourcing rules and the ledger format). To add a
  channel, add `agents/<name>.md` and include it in `FANOUT_CHANNELS`.

Environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `FANOUT_MODEL` | claude's default | Model for the writers |
| `FANOUT_EDITOR_MODEL` | `FANOUT_MODEL` | Model for the editor |
| `FANOUT_CHANNELS` | all five | Comma-separated channels to run |
| `FANOUT_TIMEOUT` | `900` | Seconds before an agent is killed |
| `FANOUT_RETRIES` | `1` | Retries for a failed agent |
| `FANOUT_MAX_BUDGET_USD` | none | Spend cap per agent |
| `FANOUT_CLAUDE_ARGS` | none | Extra flags for every `claude` call |
| `FANOUT_STRICT` | `1` | Exit non-zero when the postcheck has errors |
| `FANOUT_RUNS_DIR` | `./runs` | Where runs go |
| `FANOUT_INBOX` | `./briefs/inbox` | Where briefs are dropped |
| `FANOUT_CLAUDE` | `claude` | The binary to call |

## Failure handling

- A writer that fails is retried once. If it still fails, the editor
  reconciles the channels that did finish and is told which one is missing.
  The run is marked `partial` and the brief isn't marked as done, so the next
  `./fanout` picks it up again.
- A per-slug lock stops two runs of the same brief from colliding.
- The brief, voice file, and bank are read-only inside the run, and the drafts
  become read-only before the editor starts.

## Tests

```bash
tests/test.sh
```

Runs the whole pipeline offline against `tests/fake-claude`, a stand-in that
writes canned output with two planted problems (an anecdote used in three
channels, a figure that isn't in the brief). The tests check that the writers
run in parallel, the precheck catches both problems, the editor's fix clears
the postcheck, unchanged briefs are skipped, reruns diff against the previous
run, a failed writer produces a partial run, and an editor that fixes nothing
fails the run.
