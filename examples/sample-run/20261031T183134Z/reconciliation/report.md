# Reconciliation report

## Summary
Three non-shared anecdotes were reused: A1 in 2 channels, A2 in 4, A3 in 2. The newsletter also attached an invented "day 45" figure to E3, and several channels used numbers the brief doesn't contain. I gave each anecdote one home (longform A1, talk A2, newsletter A3; A4 stays shared). I rewrote the affected passages so they work without the story, removed the untraced figures and varied repeated phrasing. All edited ledgers now match the copy.

## Changes
| # | Channel | File | Issue type | What was wrong | What you did |
|---|---------|------|------------|----------------|--------------|
| 1 | longform | article.md | Anecdote reuse | A2 (fintech two-team pilot) had its own section, and the piece also used A1 | Rewrote "One team picked a number in week one" as "Pick the number in week one" with no story. Kept the review-turnaround reasoning and the multi-team cost point |
| 2 | longform | article.md | Anecdote reuse | The counterpoint section and the checklist both mentioned the fintech team | Made the counterpoint line general ("If a team's review turnaround stays flat…") and cut "the fintech team used review turnaround" from the checklist |
| 3 | longform | article.md | Untraced figure | "At day 30 it usually looks good": 30 isn't in the brief | Changed it to "In the first month" |
| 4 | linkedin | post-02.md | Anecdote reuse | The post was built on A1, which longform opens and closes on | Rewrote it without the story. It now opens on activation as the wrong number, and E1 and the fix are unchanged |
| 5 | linkedin | post-02.md | Untraced figure | "not day 89": 89 isn't in the brief | Changed it to "in week one, not the week before renewal" |
| 6 | linkedin | post-03.md | Anecdote reuse | The post was built on A2 | Rewrote the hook and dropped the story. The E2 data, the 3-step how-to and the multi-team close stay |
| 7 | linkedin | post-03.md | Repeated phrasing | "None of this needs a dashboard project" was close to longform's "None of this needs a data team" and the talk's "You don't need a dashboard" | Changed it to "It doesn't need new tooling" |
| 8 | linkedin | post-01.md | Scope drift | "32 interviews" (the brief says 32 companies, by interview) | Changed it to "32 companies is a small sample, gathered by interview" |
| 9 | linkedin | post-01.md | Repeated phrasing | "the 9 had evidence… The 23 had a login count" copied the structure of longform's "those 9 companies had something to show. The other 23 had a usage chart" | Rephrased it as "Only the 9 could answer the question a renewal actually asks. Everyone else was arguing from logins." |
| 10 | linkedin | post-01.md | Untraced figure | "past day 30" | Changed it to "past its first month" |
| 11 | linkedin | series-plan.md, ledger.json | Ledger | The plan and ledger listed A1 and A2 | Updated titles, sources and the anecdote note. Ledger anecdotes are now empty, and I added 2 claim entries for post-01 lines that cite figures |
| 12 | newsletter | edition.md | Anecdote reuse | The lead story, a subject line and the preview text all used A2, and the body referred to "the fintech's second team" | Made A3 the lead ("Three weeks on paper"), rewrote the subject line and preview text, and made the research section general |
| 13 | newsletter | edition.md | Figure drift | Checklist item 5 tied "day 45" to E3, and 45 isn't in the brief (precheck error) | Changed it to "a check-in at the halfway point" |
| 14 | newsletter | edition.md | Sourcing leak / reuse | Item 6 retold A3 and said "in the brief" | Changed it to "The paper log above is the model." |
| 15 | newsletter | edition.md | Repeated phrasing | "Some teams that stall are right to stall" repeated longform's line, which comes straight from the brief | Changed it to "Not every stalled pilot is a mistake." |
| 16 | talk | outline.md | Anecdote reuse | Slide 9 was built on A3, and slide 11 referred back to the "paper-log week" | Rewrote slide 9 as a week-one check with no story (sources: none) and made the slide 11 line general |
| 17 | talk | outline.md | Contradiction | Slide 9 said to watch usage "the first week or two, then lock in the measure." That conflicts with every other channel's advice: agree the measure in week one and take the baseline before seats go out | The new slide 9 does the check in week one, alongside picking the measure |
| 18 | talk | outline.md | Untraced figure | "the next 20 minutes" | Changed it to "the rest of this talk" |
| 19 | proof-points | proof-points.md | Untraced figure | "100% renewal rate" in do_not_say | Replaced it with a general ban on percentage renewal rates that covers both 9 of 9 and 11 of 23 |
| 20 | all edited | ledger.json | Ledger | Anecdote IDs and claim statements no longer matched the copy | Updated the longform, linkedin, newsletter and talk ledgers |

## Anecdote allocation
| Anecdote | Channel that keeps it | Removed from |
|----------|-----------------------|--------------|
| A1 | longform (opening scene and closing callback) | linkedin (post-02) |
| A2 | talk (title, opening, closing, and slides 3, 6, 7, 10 and 11) | longform, linkedin (post-03), newsletter |
| A3 | newsletter (now the lead story) | talk (slides 9 and 11) |
| A4 (shared) | newsletter, talk | none |

LinkedIn now has no anecdotes. The brief had no unused anecdotes to swap in, so posts 02 and 03 stand on the evidence alone.

## Left for the author
1. **The brief is labelled as invented examples.** Every organisation and figure in the package (Northfield, Halvorsen, Ostrava) is a placeholder. Proof-points already flags this with a TK, but it marks every entry `confidence: VERIFIED`, which only means "matches the brief." Decide whether to downgrade those entries until real research replaces the brief.
2. **Open TKs: 9 in total.** Proof-points has 7 (source reality check, survey geography, subgroup sizes, Halvorsen sample details, Ostrava setting). The talk has 2, both slide 13: the fintech team's actual review turnaround figures.
3. **Figure-attribution warnings, not changed.** LinkedIn post-03 and proof-points cite "Northfield Developer Survey 2026" with E2. LinkedIn post-04 and proof-points cite "Halvorsen Research's 2026 report" with E4. In both cases the year is part of the source name the brief gives under E1/E3, so I treated it as attribution, not drift.
4. **Author advice with no source.** The checks below are the author's practical advice, not brief facts. Confirm you're happy to state them as advice:
   - longform's "a month of pre-pilot data"
   - the newsletter's halfway check-in and "another 90 days of drift"
   - the talk's statement that the first weeks go on rollout
5. **Interpretive phrasing.** The newsletter says the no-measure group "collapses" (78% to 41%) and that measuring made renewal "a decision instead of a coin toss." Both fit the data, but they are stronger than the brief's wording.
6. **Longform `word_count: 2050` in the front matter** wasn't recounted after the section rewrite. The length is roughly the same.
