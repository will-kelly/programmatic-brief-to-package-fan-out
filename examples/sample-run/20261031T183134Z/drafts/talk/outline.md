---
talk_title: "Two teams, one pilot: what day 90 actually asks for"
abstract: "Most AI coding assistant pilots don't fail on model quality. They stall around day 90, when the renewal decision arrives and nobody can say what changed. This talk follows a fintech director's two-team pilot: one team agreed in week one to track review turnaround, and the other team had no numbers at all. Drawing on the Northfield Developer Survey 2026, Halvorsen Research's 2026 report on 32 companies, and a 2025 Ostrava University study that cuts the other way, it shows why seat activation is the wrong evidence and what to measure instead. For engineering directors and platform leads at companies with 200 to 2,000 developers."
duration_minutes: 20
slide_count: 13
---

## Slide 1: Two teams, one pilot
- on_slide: One fintech pilot. Two teams. Only one had numbers.
- visual: Two columns labelled "Team 1" and "Team 2". Team 1 has a heading, "review turnaround". Team 2's column is empty.
- speaker_notes: A director at a fintech ran a coding assistant pilot across two teams. Same pilot, same renewal decision at the end. In week one, one of those teams agreed to track a single thing: review turnaround. The other team didn't agree to track anything. When renewal came round, the first team's numbers made the case. The second team's numbers didn't exist. They weren't bad numbers. There were no numbers. I want to spend the next 20 minutes on why that second team is the normal case, and on what the first team did that you can copy at your next kickoff.
- minutes: 2
- sources: A2

## Slide 2: You get about one quarter
- on_slide: 94 days: the median pilot before a renewal decision
- visual: Single number, "94 days", with source line: Halvorsen Research, "Platform teams and AI tooling," May 2026, 32 companies.
- speaker_notes: This is the clock you're on. Halvorsen Research interviewed 32 companies for a 2026 report on platform teams. The median pilot ran 94 days before a renewal decision. That feels like plenty of time at kickoff. It isn't, because the first weeks go on rollout and getting people to try the tool at all. By the time usage settles, the renewal meeting is already on the calendar. Whatever evidence you plan to bring to that meeting, you have to decide to collect it at the start.
- minutes: 1
- sources: E3

## Slide 3: Most pilots start without a target
- on_slide: 61% said their pilot had no agreed success measure
- visual: Single number, "61%", with source line: Northfield Developer Survey 2026, n=1,240 developers, fielded March 2026.
- speaker_notes: So how many teams decide at the start? Northfield surveyed 1,240 developers in March 2026. 61% said their company's assistant pilot had "no agreed success measure" at launch. Look at who answered: developers, describing their own company's pilot. These are the people using the tool, saying nobody agreed with them what success looked like. If you're the director or platform lead, you may believe a measure existed. What matters is whether the team agreed to it. In the fintech pilot, that week-one agreement is what separated the two teams.
- minutes: 1.5
- sources: E1, A2

## Slide 4: Usage drops faster without a measure
- on_slide: Without a measure, weekly use fell from 78% to 41%
- visual: Line chart of E2. Two lines from month one to month three: pilots with no success measure, 78% to 41%; pilots with one, 80% to 66%.
- speaker_notes: The same survey tracked weekly active use. Among pilots with no success measure, it fell from 78% in month one to 41% by month three. Among pilots that had one, it fell from 80% to 66%. Both lines go down, so novelty wears off everywhere. But one group ends month three at 66% and the other at 41%. My read is that when a team knows what it's trying to change, people keep using the tool for that job. When nobody knows, use drifts, and by renewal there's less to look at.
- minutes: 1.5
- sources: E2

## Slide 5: Activation answers the wrong question
- on_slide: Seat activation counts logins. Renewal asks what changed.
- visual: Simple diagram. Left box, "seat activation", greyed out. Arrow to right box, "changed work", highlighted.
- speaker_notes: This is the core of the talk. Most coding assistant pilots don't fail on model quality. They stall around day 90 because the organisation measured seat activation instead of changed work. Activation is easy to count, so it's what gets counted. But it answers a question nobody in the renewal meeting is asking. Whoever holds the budget wants to know how the work is different now. If you didn't measure the work, you walk into that meeting with no evidence either way. You don't get a yes or a no. You get a shrug.
- minutes: 1
- sources: none (thesis)

## Slide 6: Teams that measured work all renewed
- on_slide: Tracked cycle time or review load: 9 of 9 renewed
- visual: Single number, "9 of 9", with source line: Halvorsen Research, May 2026.
- speaker_notes: Back to Halvorsen's 32 companies. 9 of them tracked any change in cycle time or review load during the pilot. All 9 renewed. Notice the word "any". These weren't controlled experiments. Each team picked something that reflects how work moves through it and watched that. It's what the fintech team did with review turnaround. It's a small group, 9 companies, so I won't tell you that measuring guarantees a renewal. What it does is give the renewal meeting something real to decide on.
- minutes: 1.5
- sources: E4, A2

## Slide 7: Teams that measured logins were split
- on_slide: Tracked only seat activation: 11 of 23 renewed
- visual: Single number, "11 of 23", with source line: Halvorsen Research, May 2026.
- speaker_notes: The other 23 companies tracked only seat activation. 11 of them renewed. Some of the decisions in that group were probably right, in both directions. But none of them rested on evidence about the work, because nobody had collected any. That includes the 11 that renewed. They renewed without knowing whether the tool had changed anything. This is the second fintech team at scale. Their pilot might have been working well. Nobody could say, so nobody could argue for it.
- minutes: 1.5
- sources: E4, A2

## Slide 8: Sometimes stalling is the right call
- on_slide: 400 pull requests, no measurable change in review time
- visual: Single number, "400", with source line: Ostrava University, "Assistant use and review latency," November 2025.
- speaker_notes: I want to be fair to the other side. A 2025 Ostrava University study of 400 pull requests found no measurable change in review time with assistant use. If that's what your team would find, then stalling at day 90 is the correct outcome. Measuring won't guarantee a renewal. What it gives you is a decision you can defend in either direction. A clear no, backed by numbers, is a good pilot result. It tells you where the money shouldn't go next time.
- minutes: 1.5
- sources: E5

## Slide 9: Watch what people actually use it for
- on_slide: One manager's paper log: mostly documentation lookups, not code
- visual: Illustrative mock-up of a handwritten log page headed "things I'd have searched for", one line per day. Label it as a reconstruction.
- speaker_notes: How do you pick what to measure? One engineering manager did something very low-tech. Every day for three weeks, they kept a paper log of "things I'd have searched for." What they found was that most of their assistant use replaced documentation lookups, not code writing. That matters for your measure. If you'd set your target around code output, you'd be measuring the wrong part of the job. Spend the first week or two watching what people actually use the tool for, then lock in the measure.
- minutes: 1.5
- sources: A3

## Slide 10: Put a name on the measurement plan
- on_slide: Name one owner for the measurement plan in week one
- visual: Calendar strip of the pilot. Week one circled. A later week marked "budget cut" in red.
- speaker_notes: Now my own mistake. In 2024 I advised on a pilot where nobody owned the measurement plan. It stayed that way until the week the budget was cut. By then there was nothing to collect and nobody to collect it. Compare that with the fintech pilot, where the team that made the renewal case agreed on its measure in week one. Put a name next to the measurement plan at kickoff. Have that person show the numbers at every check-in, so the last meeting isn't the first time anyone sees them.
- minutes: 1.5
- sources: A4, A2

## Slide 11: Pick one measure of changed work
- on_slide: One measure: cycle time or review load. Start there.
- visual: Two cards side by side, "cycle time" and "review load". Below them, a smaller card: "fintech team: review turnaround".
- speaker_notes: You don't need a dashboard. The 9 Halvorsen companies that all renewed tracked any change in cycle time or review load. The fintech team picked review turnaround. Pick one, take a baseline before the tool goes out, and check it at the same interval every time. If your paper-log week tells you people mostly use the tool for lookups, choose something that would show that, and say so at the start. The measure has to be agreed by the team and honest about what it can and can't show.
- minutes: 1.5
- sources: E4, A2, A3

## Slide 12: What to bring to day 90
- on_slide: Bring a before-and-after, then your recommendation
- visual: Mock renewal slide: a before-and-after bar for one measure, values labelled "your numbers", and a line underneath reading "Recommendation: renew / stop".
- speaker_notes: Picture the renewal meeting. Someone asks what changed. A seat-activation chart doesn't answer that, however high the line is. What answers it is a before-and-after on the measure your team agreed in week one, plus your recommendation. If the line didn't move, as with the 400 pull requests in the Ostrava study, recommend stopping and show why. You've still run a good pilot. The one result you can't defend is no result.
- minutes: 1
- sources: E5

## Slide 13: Back to the two teams
- on_slide: Be the team with numbers, whatever they say
- visual: Slide 1's two columns again. Team 1's column now filled with its review turnaround figures [[TK: the fintech team's actual review turnaround figures, if the director will share them]]. Team 2's column still empty.
- speaker_notes: Back to the fintech. Two teams, one pilot. One agreed in week one to track review turnaround, and its numbers made the renewal case. The other team's numbers didn't exist. [[TK: the fintech team's actual review turnaround figures, if the director will share them]]. The tool didn't decide that renewal. The week-one agreement did. The median pilot gets 94 days. Spend the first week of yours agreeing what changed work looks like for your team, and put someone's name on it.
- minutes: 2
- sources: A2, E3
