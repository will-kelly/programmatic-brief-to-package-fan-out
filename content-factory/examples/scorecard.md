# Content factory scorecard

## Visibility in answers

| Survey | Unbranded answers | Mentioned | 95% CI | Picked first | Wrong about Render (firm / disputed) | Registry coverage |
|---|---|---|---|---|---|---|
| 2026-11-04 (claude) | 84 | 89% | 81%–94% | 14% | 0 / 3 of 108 | 40% |

Target clusters in the latest survey:

- ai-agents: 71% (95% CI 50%–86%)
- python-stacks: 100% (95% CI 76%–100%)
- js-stacks: 100% (95% CI 76%–100%)

A move between surveys counts only when the intervals stop overlapping. Anything else is sampling noise. Firm means a known-wrong pattern or a human confirmed it; disputed means only the model judge flagged it.

## Accuracy and review cost

- 6 drafts checked (1 from partners), 82 claims
- 1 contradicted claims caught before publishing
- auto-verified share of claims: 0% (corroborated against a fixture or seed facts: 99%)
- estimated expert review: 11.6 min per piece (vs 37.3 unassisted). Both are the time model in pipeline.py until `cf review done` records real minutes.

## Catalog and freshness

- 1 published pages, 4 tracked claims
- 0 claims on the refresh queue, 0 no longer hold

## Spend

- survey-judge: $4.05
- survey-answer: $3.60
- claim-judge: $1.07
- draft: $0.36
- claim-extract: $0.02

## Partners

| Partner | Drafts | Ready on first check | Contradicted per draft | Lint errors per draft |
|---|---|---|---|---|
| partner:acme-content | 1 | 0% | 1.0 | 3.0 |

Signups attributed to content aren't in this scorecard until there's a join between page views and signup source. Don't fake that number.

