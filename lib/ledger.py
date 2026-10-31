#!/usr/bin/env python3
"""Mechanical checks and bookkeeping for a fan-out run.

Subcommands:
  check   Read every channel ledger in a run stage and report anecdote reuse,
          figures that don't trace to the brief, unknown IDs, missing files,
          and length violations. Writes <out>.json and <out>.md.
  costs   Summarise the claude JSON logs in a run into manifest fields.
  slug    Print the slug for a brief (front matter `slug:` or the filename).
  hash    Print the sha256 of a file.

Standard library only, so it runs anywhere Python 3.8+ does.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ID_RE = re.compile(r"\[([A-Z]{1,2}\d{1,3})\]")
TK_RE = re.compile(r"\[\[TK:[^\]]*\]\]")
NUM_RE = re.compile(
    r"(?<![\w.])([$€£])?(\d{1,3}(?:,\d{3})+|\d+)(\.\d+)?\s?(%|percent\b|x\b|k\b|K\b|M\b|B\b|bn\b|million\b|billion\b)?"
)
DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
# Lines that carry structural numbers, not claims.
SKIP_LINE_RE = re.compile(
    r"^\s*(-\s*)?(word_count|minutes|duration_minutes|slide_count|recheck_by|evidence_id|replaces)\s*:"
    r"|^\s*#{1,6}\s*(slide|post)\s*\d+"
    r"|^\s*\|",
    re.IGNORECASE,
)
LINKEDIN_HARD_MAX = 3000


# --------------------------------------------------------------------------
# Brief parsing


def parse_brief(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    entries: dict[str, str] = {}
    shared: set[str] = set()
    for i, line in enumerate(lines):
        ids = ID_RE.findall(line)
        if not ids:
            continue
        # An entry is the tagged line plus following lines up to a blank line
        # or the next tagged line.
        block = [line]
        for nxt in lines[i + 1 :]:
            if not nxt.strip() or ID_RE.search(nxt):
                break
            block.append(nxt)
        body = "\n".join(block)
        for ident in ids:
            # First definition wins; later mentions are cross-references.
            entries.setdefault(ident, body)
            if "(shared)" in line.lower():
                shared.add(ident)
    return {
        "text": text,
        "entries": entries,
        "anecdotes": sorted(i for i in entries if i.startswith("A")),
        "evidence": sorted(i for i in entries if not i.startswith("A")),
        "shared": shared,
        "numbers": {n for n, _ in numbers_in(text)},
    }


def norm_number(m: re.Match) -> str:
    whole = m.group(2).replace(",", "")
    frac = m.group(3) or ""
    unit = (m.group(4) or "").lower()
    if unit == "percent":
        unit = "%"
    return f"{whole}{frac}{unit if unit == '%' else ''}"


def numbers_in(text: str):
    """Yield (normalised number, raw match) for every number in text."""
    for line in text.splitlines():
        if SKIP_LINE_RE.search(line):
            continue
        clean = DATE_RE.sub(" ", line)
        for m in NUM_RE.finditer(clean):
            yield norm_number(m), m.group(0).strip()


def is_year(normed: str) -> bool:
    return normed.isdigit() and 1900 <= int(normed) <= 2100


def is_claimlike(raw: str, normed: str) -> bool:
    """Numbers worth tracing: percentages, money, multipliers, or >= 11."""
    if "%" in normed or raw[:1] in "$€£":
        return True
    if re.search(r"(x|k|m|b|bn|million|billion)$", raw.lower()):
        return True
    try:
        val = float(normed.rstrip("%"))
    except ValueError:
        return False
    # Years and small counts ("3 steps") are noise.
    if 1900 <= val <= 2100 and "." not in normed:
        return False
    return val >= 11


# --------------------------------------------------------------------------
# check


def load_ledger(chan_dir: Path) -> tuple[dict | None, str | None]:
    p = chan_dir / "ledger.json"
    if not p.exists():
        return None, "ledger.json is missing"
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return None, f"ledger.json is not valid JSON ({e})"
    if not isinstance(data, dict):
        return None, "ledger.json is not an object"
    for key in ("files", "anecdotes", "claims"):
        data.setdefault(key, [])
    data.setdefault("gaps", [])
    return data, None


def cmd_check(args) -> int:
    run = Path(args.run)
    stage = run / args.stage
    brief = parse_brief(run / "brief.md")
    channels = [c for c in args.channels.split(",") if c]
    issues: list[dict] = []
    usage: dict[str, dict[str, list[str]]] = {"anecdotes": {}, "evidence": {}}
    theses: dict[str, str] = {}
    tk_count: dict[str, int] = {}

    def add(sev, kind, channel, msg, file=None):
        issues.append({"severity": sev, "type": kind, "channel": channel, "file": file, "message": msg})

    for ch in channels:
        cdir = stage / ch
        if not cdir.is_dir():
            add("error", "missing-channel", ch, f"no output directory at {args.stage}/{ch}")
            continue
        led, err = load_ledger(cdir)
        if err:
            add("error", "ledger", ch, err)
            continue
        theses[ch] = str(led.get("thesis", "")).strip()

        # Files
        for f in led["files"]:
            if not (cdir / f).is_file():
                add("error", "missing-file", ch, f"ledger lists {f} but it doesn't exist", f)
        copy_files = sorted(p for p in cdir.rglob("*") if p.is_file() and p.name != "ledger.json")
        listed = set(led["files"])
        for p in copy_files:
            rel = str(p.relative_to(cdir))
            if rel not in listed:
                add("warning", "unlisted-file", ch, f"{rel} exists but isn't in the ledger", rel)

        # Anecdotes
        seen_here: set[str] = set()
        for a in led["anecdotes"]:
            aid = str(a.get("id", "")).strip()
            if not aid:
                continue
            if brief["entries"] and aid not in brief["entries"]:
                add("error", "unknown-id", ch, f"anecdote {aid} isn't in the brief (possible invention)", a.get("file"))
            if aid not in seen_here:
                usage["anecdotes"].setdefault(aid, []).append(ch)
                seen_here.add(aid)

        # Claims and figures
        seen_ev: set[str] = set()
        for c in led["claims"]:
            cid = str(c.get("id", "")).strip()
            if not cid:
                add("warning", "untagged-claim", ch, f"claim without an ID: {c.get('statement', '')[:80]}", c.get("file"))
                continue
            if brief["entries"] and cid not in brief["entries"]:
                add("error", "unknown-id", ch, f"evidence {cid} isn't in the brief", c.get("file"))
                continue
            if cid not in seen_ev:
                usage["evidence"].setdefault(cid, []).append(ch)
                seen_ev.add(cid)
            entry = brief["entries"].get(cid, "")
            entry_nums = {n for n, _ in numbers_in(entry)}
            for fig in c.get("figures", []) or []:
                # Years are usually part of a source name ("Survey 2026"), not a claim.
                nums = [n for n, _ in numbers_in(str(fig)) if not is_year(n)]
                for n in nums:
                    if n not in entry_nums and n not in brief["numbers"]:
                        add("error", "figure-drift", ch,
                            f"{cid} is cited with {fig!r}, which isn't in the brief", c.get("file"))
                    elif entry and n not in entry_nums:
                        add("warning", "figure-attribution", ch,
                            f"{cid} is cited with {fig!r}, which the brief gives elsewhere, not in {cid}", c.get("file"))

        # Copy-level scans
        tks = 0
        for p in copy_files:
            rel = str(p.relative_to(cdir))
            try:
                text = p.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            tks += len(TK_RE.findall(text))
            untraced = sorted({raw for n, raw in numbers_in(text)
                               if is_claimlike(raw, n) and n not in brief["numbers"]})
            if untraced:
                add("warning", "untraced-figure", ch,
                    "figures not found anywhere in the brief: " + ", ".join(untraced[:12]), rel)
            if ch == "linkedin" and rel.startswith("post-"):
                n_chars = len(text.strip())
                if n_chars > LINKEDIN_HARD_MAX:
                    add("error", "length", ch, f"{rel} is {n_chars} characters (max {LINKEDIN_HARD_MAX})", rel)
        tk_count[ch] = tks

    # Cross-channel anecdote reuse (proof points are exempt: they're a bank).
    for aid, chans in sorted(usage["anecdotes"].items()):
        writers = [c for c in chans if c != "proof-points"]
        if len(writers) > 1 and aid not in brief["shared"]:
            add("error", "anecdote-reuse", ",".join(writers),
                f"{aid} is used in {len(writers)} channels: {', '.join(writers)}")

    unused = [a for a in brief["anecdotes"] if a not in usage["anecdotes"]]
    errors = sum(1 for i in issues if i["severity"] == "error")
    warnings = sum(1 for i in issues if i["severity"] == "warning")
    result = {
        "stage": args.stage,
        "channels": channels,
        "errors": errors,
        "warnings": warnings,
        "issues": issues,
        "anecdote_usage": usage["anecdotes"],
        "evidence_usage": usage["evidence"],
        "unused_anecdotes": unused,
        "shared_anecdotes": sorted(brief["shared"]),
        "theses": theses,
        "tk_count": tk_count,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    out.with_suffix(".md").write_text(render_md(result, brief), encoding="utf-8")
    print(f"{args.stage}: {errors} errors, {warnings} warnings")
    return 1 if (args.strict and errors) else 0


def render_md(r: dict, brief: dict) -> str:
    out = [f"# Mechanical check: {r['stage']}", "",
           f"{r['errors']} errors, {r['warnings']} warnings across {len(r['channels'])} channels.", ""]
    out += ["## Issues", ""]
    if r["issues"]:
        out += ["| Severity | Type | Channel | File | Detail |", "|---|---|---|---|---|"]
        order = {"error": 0, "warning": 1}
        for i in sorted(r["issues"], key=lambda x: (order[x["severity"]], x["type"], x["channel"])):
            detail = i["message"].replace("|", "\\|")
            out.append(f"| {i['severity']} | {i['type']} | {i['channel']} | {i['file'] or ''} | {detail} |")
    else:
        out.append("None.")
    out += ["", "## Anecdote usage", ""]
    if brief["anecdotes"]:
        out += ["| Anecdote | Used in | Shared in brief |", "|---|---|---|"]
        for a in brief["anecdotes"]:
            used = ", ".join(r["anecdote_usage"].get(a, [])) or "unused"
            out.append(f"| {a} | {used} | {'yes' if a in brief['shared'] else 'no'} |")
    else:
        out.append("The brief has no tagged anecdotes.")
    out += ["", "Unused anecdotes available for swaps: " + (", ".join(r["unused_anecdotes"]) or "none"), ""]
    out += ["## Evidence usage", "", "| Evidence | Used in |", "|---|---|"]
    for e in brief["evidence"]:
        out.append(f"| {e} | {', '.join(r['evidence_usage'].get(e, [])) or 'unused'} |")
    out += ["", "## Thesis as each channel states it", ""]
    for ch, t in r["theses"].items():
        out.append(f"- **{ch}:** {t or '(none given)'}")
    out += ["", "## Open TKs", ""]
    for ch, n in r["tk_count"].items():
        out.append(f"- {ch}: {n}")
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------
# costs, slug, hash


def cmd_costs(args) -> int:
    logs = Path(args.run) / "logs"
    agents = {}
    total = 0.0
    for p in sorted(logs.glob("[!.]*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            agents[p.stem] = {"error": "unreadable log"}
            continue
        cost = float(d.get("total_cost_usd") or 0)
        total += cost
        agents[p.stem] = {
            "cost_usd": round(cost, 4),
            "duration_s": round((d.get("duration_ms") or 0) / 1000, 1),
            "turns": d.get("num_turns"),
            "is_error": bool(d.get("is_error")),
            "result": (d.get("result") or "")[:500],
        }
    print(json.dumps({"agents": agents, "total_cost_usd": round(total, 4)}))
    return 0


def cmd_slug(args) -> int:
    p = Path(args.brief)
    text = p.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    if m:
        s = re.search(r"^slug:\s*(\S+)", m.group(1), re.M)
        if s:
            print(re.sub(r"[^a-z0-9-]+", "-", s.group(1).lower()).strip("-"))
            return 0
    print(re.sub(r"[^a-z0-9-]+", "-", p.stem.lower()).strip("-") or "brief")
    return 0


def cmd_hash(args) -> int:
    print(hashlib.sha256(Path(args.file).read_bytes()).hexdigest())
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("--run", required=True)
    c.add_argument("--stage", required=True, choices=["drafts", "final"])
    c.add_argument("--channels", required=True)
    c.add_argument("--out", required=True, help="output path without extension")
    c.add_argument("--strict", action="store_true", help="exit 1 if errors remain")
    c.set_defaults(fn=cmd_check)
    k = sub.add_parser("costs")
    k.add_argument("--run", required=True)
    k.set_defaults(fn=cmd_costs)
    s = sub.add_parser("slug")
    s.add_argument("brief")
    s.set_defaults(fn=cmd_slug)
    h = sub.add_parser("hash")
    h.add_argument("file")
    h.set_defaults(fn=cmd_hash)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
