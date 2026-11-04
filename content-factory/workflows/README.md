# Render Workflows binding

`render_workflows.py` maps the factory's stages onto Render Workflows tasks.
The stages themselves live in `factory/` and don't import the SDK, so they
run the same on a laptop (`./cf ...`) and on Render.

Two tasks matter:

- `weekly_cycle` snapshots the docs, fans the survey out one task per
  topic cluster, rebuilds the refresh queue, and re-ranks the backlog.
- `produce` takes one brief through research, draft, and check, and stops
  at the review packet. Publishing waits for a person.

Before deploying, check the three `VERIFY` notes in the file against the
Python SDK reference for the version you pin. They were written from the
documented pattern without access to the live reference.
