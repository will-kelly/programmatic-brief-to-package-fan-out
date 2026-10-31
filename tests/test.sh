#!/usr/bin/env bash
# Offline end-to-end tests for fanout, using tests/fake-claude.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'chmod -R u+w "$TMP" 2>/dev/null; rm -rf "$TMP"' EXIT

export FANOUT_CLAUDE="$ROOT/tests/fake-claude"
export FANOUT_RUNS_DIR="$TMP/runs"
export FANOUT_INBOX="$TMP/inbox"
export FAKE_SLEEP=2
export FAKE_TRACE="$TMP/trace"
mkdir -p "$FANOUT_INBOX"
cp "$ROOT/examples/ai-pilot-stall.md" "$FANOUT_INBOX/"

pass=0 fail=0
ok()   { pass=$((pass + 1)); printf '  ok    %s\n' "$1"; }
bad()  { fail=$((fail + 1)); printf '  FAIL  %s\n' "$1"; }
check(){ if eval "$2"; then ok "$1"; else bad "$1"; fi; }
jq_()  { python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print(eval(sys.argv[2]))' "$@"; }

FANOUT="$ROOT/fanout"
SLUG_DIR="$FANOUT_RUNS_DIR/ai-pilot-stall"

echo "1. inbox run"
"$FANOUT" >"$TMP/out1" 2>&1; rc=$?
check "exit 0" "[[ $rc -eq 0 ]]"
RUN="$SLUG_DIR/$(readlink "$SLUG_DIR/latest")"
check "latest symlink points at a run" "[[ -d '$RUN' ]]"
for ch in longform linkedin newsletter proof-points talk; do
  check "draft and final for $ch" "[[ -f '$RUN/drafts/$ch/ledger.json' && -f '$RUN/final/$ch/ledger.json' ]]"
done
check "outcome ok" "[[ \$(jq_ '$RUN/manifest.json' 'd[\"outcome\"]') == ok ]]"
check "precheck caught A1 reuse" "grep -q 'A1 is used in 3 channels' '$RUN/reconciliation/precheck.md'"
check "precheck caught E2 figure drift" "grep -q \"E2 is cited with '45%'\" '$RUN/reconciliation/precheck.md'"
check "postcheck clean" "[[ \$(jq_ '$RUN/reconciliation/postcheck.json' 'd[\"errors\"]') == 0 ]]"
check "editor report written" "[[ -s '$RUN/reconciliation/report.md' ]]"
check "editor.diff shows the fix" "grep -q '^+Active use fell to 41%' '$RUN/reconciliation/editor.diff'"
check "drafts untouched by editor" "grep -q '45%' '$RUN/drafts/newsletter/edition.md'"
check "brief is read-only in the run" "[[ ! -w '$RUN/brief.md' || \$(id -u) -eq 0 ]]"
check "manifest records input hashes" "[[ \$(jq_ '$RUN/manifest.json' 'len(d[\"inputs_sha256\"])') -ge 8 ]]"

echo "2. writers ran in parallel"
starts=$(grep -c ' start$' "$FAKE_TRACE")
first_end_line=$(grep -n ' end$' "$FAKE_TRACE" | head -1 | cut -d: -f1)
starts_before_end=$(head -n "$((first_end_line - 1))" "$FAKE_TRACE" | grep -c ' start$')
check "all 5 writers started before any finished" "[[ $starts_before_end -eq 5 ]]"
wall=$(jq_ "$RUN/manifest.json" 'd["wall_clock_s"]')
check "wall clock ${wall}s is well under serial 12s" "[[ $wall -lt 9 ]]"
check "6 agent runs recorded" "[[ $starts -eq 6 ]]"

echo "3. unchanged brief is skipped"
before=$(ls "$SLUG_DIR" | wc -l)
"$FANOUT" >/dev/null 2>&1
check "no new run" "[[ \$(ls '$SLUG_DIR' | wc -l) -eq $before ]]"

echo "4. --force reruns and diffs against the previous run"
sleep 1
"$FANOUT" run "$FANOUT_INBOX/ai-pilot-stall.md" --force >/dev/null 2>&1; rc=$?
RUN2="$SLUG_DIR/$(readlink "$SLUG_DIR/latest")"
check "exit 0" "[[ $rc -eq 0 ]]"
check "new run dir" "[[ '$RUN2' != '$RUN' ]]"
check "vs-previous.diff written" "[[ -f '$RUN2/reconciliation/vs-previous.diff' ]]"
check "manifest names previous run" "[[ \$(jq_ '$RUN2/manifest.json' 'd[\"previous_run\"]') == \$(basename '$RUN') ]]"
check "fanout diff runs" "'$FANOUT' diff ai-pilot-stall >/dev/null"
check "fanout list shows 2 runs" "[[ \$('$FANOUT' list ai-pilot-stall | wc -l) -eq 2 ]]"

echo "5. a failed writer gives a partial run, editor still reconciles the rest"
sleep 1
FAKE_FAIL=talk FANOUT_RETRIES=0 "$FANOUT" run "$FANOUT_INBOX/ai-pilot-stall.md" --force >/dev/null 2>&1; rc=$?
RUN3="$SLUG_DIR/$(readlink "$SLUG_DIR/latest")"
check "exit non-zero" "[[ $rc -ne 0 ]]"
check "outcome partial" "[[ \$(jq_ '$RUN3/manifest.json' 'd[\"outcome\"]') == partial ]]"
check "talk marked failed" "[[ \$(jq_ '$RUN3/manifest.json' 'd[\"status\"][\"talk\"]') == failed ]]"
check "editor still ran" "[[ \$(jq_ '$RUN3/manifest.json' 'd[\"status\"][\"editor\"]') == ok ]]"
check "editor told which writer failed" "grep -q 'failed and produced nothing.* talk' '$RUN3/prompts/editor.md'"
check "lock released" "[[ ! -e '$SLUG_DIR/.lock' ]]"

echo "6. an editor that fixes nothing fails the postcheck"
sleep 1
FAKE_EDITOR_NOOP=1 "$FANOUT" run "$FANOUT_INBOX/ai-pilot-stall.md" --force >"$TMP/out6" 2>&1; rc=$?
RUN4="$SLUG_DIR/$(readlink "$SLUG_DIR/latest")"
check "exit non-zero" "[[ $rc -ne 0 ]]"
check "outcome needs-review" "[[ \$(jq_ '$RUN4/manifest.json' 'd[\"outcome\"]') == needs-review ]]"
check "summary lists unresolved reuse" "grep -q 'anecdote-reuse' '$TMP/out6'"

echo "7. ledger flags IDs that aren't in the brief"
R="$TMP/unit"; mkdir -p "$R/drafts/talk"
cp "$ROOT/examples/ai-pilot-stall.md" "$R/brief.md"
echo '{"files":[],"anecdotes":[{"id":"A9"}],"claims":[{"id":"E1","figures":["61%"]}]}' >"$R/drafts/talk/ledger.json"
python3 "$ROOT/lib/ledger.py" check --run "$R" --stage drafts --channels talk --out "$R/c" >/dev/null
check "A9 flagged as possible invention" "grep -q 'A9 isn.t in the brief' '$R/c.md'"
check "E1 at 61% is clean" "! grep -q 'figure-drift' '$R/c.md'"

echo
echo "$pass passed, $fail failed"
[[ $fail -eq 0 ]]
