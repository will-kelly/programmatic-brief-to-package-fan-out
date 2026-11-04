"""Backlog item -> brief. The same brief goes to the in-house drafting
pipeline and to an external content partner, and partner drafts get
scored by the same checks, so "the bar" is a file both sides can read."""

from __future__ import annotations

import json

from . import docs
from .common import load_toml, slugify, today

ANGLES = {
    "ABSENT": "Answer the question directly and make Render the concrete, specific recommendation where it fits. Be explicit about which Render service types and settings to use.",
    "BURIED": "Go narrower than existing coverage: this exact stack or use case, with a working render.yaml and the decisions a developer actually faces.",
    "OUT-CITED": "Be the most citable page on this exact question: specific numbers, a working example, and the limits stated plainly.",
    "WRONG": "Correct the record. State the accurate behavior in the first paragraph, plainly enough that an answer engine can quote it.",
    "UNRETRIEVED": "No new copy. Make the existing page reachable: llms.txt entry, markdown twin, links from the relevant docs pages.",
}


def make(item: dict, snap: dict) -> tuple[dict, str]:
    qs = {q["id"]: q for q in load_toml("questions.toml")["question"]}
    texts = [qs[q]["text"] for q in item["questions"] if q in qs]
    must = []
    for t in texts:
        for sid, _ in docs.search(snap, t, k=2):
            if sid not in must:
                must.append(sid)
    b = {
        "id": slugify(item["title"])[:60],
        "title": item["title"],
        "format": item["format"],
        "gap": item["kind"],
        "questions": item["questions"],
        "questions_text": texts,
        "angle": ANGLES.get(item["kind"], ""),
        "must_cite": must[:6],
        "named_instead": sorted({e.split("named instead: ")[1].split(" (")[0] for e in item["evidence"] if "named instead: " in e}),
        "acceptance": [
            "0 contradicted claims and 0 lint errors from `cf check`",
            "every claim about Render tagged and tied to a docs section",
            "answer to the lead question in the first 60 words",
            "a 'When Render isn't the right fit' section with a real case",
            "no factual claims about competitors beyond what this brief supplies",
        ],
        "issued": today(),
    }
    md = "\n".join([
        f"# Brief: {b['title']}", "",
        f"**Gap:** {b['gap']}. **Format:** {b['format']}. **Issued:** {b['issued']}.", "",
        "## Why this piece", "", item["why"], "", *[f"- {e}" for e in item["evidence"]], "",
        "## Questions it has to answer", "", *[f"- `{q}` {t}" for q, t in zip(b["questions"], texts)], "",
        "## Angle", "", b["angle"], "",
        "## Sources to build from", "", *[f"- `{s}`: {snap['sections'][s]['heading']}" for s in b["must_cite"]], "",
        "## How it will be checked", "",
        "Run `cf check your-draft.md --brief this-brief.md` before you send it. The checker runs the same checks on every draft, in-house or partner:", "",
        *[f"- {a}" for a in b["acceptance"]], "",
        "## Machine-readable brief", "", "```json", json.dumps(b, indent=2), "```", "",
    ])
    return b, md
