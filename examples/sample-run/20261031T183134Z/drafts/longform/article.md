---
title: AI coding pilots stall at day 90 because nobody measured the work
dek: The renewal meeting asks what changed, and most pilots only tracked who logged in, which leaves no answer either way.
word_count: 2050
---

The meeting was set for day 90. A platform lead at a logistics company came in with a deck, and the CFO asked one question: what had changed? The only slide that tried to answer it was a seat-activation chart. It showed 92%.

That number looks like success. It tells you that almost everyone who got the tool switched it on. It doesn't tell you whether pull requests merged faster, whether reviewers spent less time on each change, or whether anyone shipped something they otherwise wouldn't have. The CFO asked about the work, and the chart only covered the licences.

I've come to think that meeting is how most AI coding assistant pilots end, and the problem in the room has little to do with the model. Most pilots don't fail on model quality. They stall around day 90 because the organisation measured seat activation instead of changed work, so when the renewal decision arrives there's no evidence either way. A budget holder with no evidence in front of them has no reason to keep paying, and no grounds to say the tool failed either.

## The renewal date arrives before anyone agrees what to measure

Halvorsen Research interviewed platform teams at 32 companies for its May 2026 report, "Platform teams and AI tooling." The median pilot in that group ran 94 days before a renewal decision.

Ninety-four days is enough to learn something if measurement starts on day one. It isn't enough if the first month goes on rolling out access, the second on watching usage climb, and the third on realising you needed a baseline you never took. Cycle time and review load only mean something as comparisons. If nobody recorded them before the assistant arrived, nobody can show they moved.

And most teams don't start measuring on day one, because most teams haven't agreed what to measure. The Northfield Developer Survey 2026 asked 1,240 developers in March 2026 about their company's assistant pilot. 61% said the pilot had "no agreed success measure" at launch.

That figure comes from developers, not from the people running the pilots. Some of those pilots may well have had a measure written down somewhere that never reached the teams using the tool. For the renewal meeting the result is the same. If the developers don't know what's being measured, they aren't working with it in mind, and nobody is collecting it from them.

So the clock and the plan are out of step. The decision date is fixed by a budget cycle. The measurement plan, if it exists, gets drafted when someone senior asks for it, and by then the useful comparison window has closed.

## Activation is the number you get for free

Seat activation wins by default. The vendor dashboard reports it. Your identity provider can confirm it. It needs no baseline and no agreement between teams. At day 30 it usually looks good, which makes it feel like progress.

The weakness is that activation records the start of adoption and nothing after it. A developer who turned the assistant on in week one and stopped using it in week five still counts as activated. The chart at the logistics company's day-90 meeting couldn't say whether people were still using the tool, and it wasn't built to.

The Northfield survey does say something about that, and it's not encouraging for pilots without a target. It split pilots by whether they had a success measure. Among pilots with no success measure, weekly active use fell from 78% in month one to 41% by month three. Among pilots that had one, it fell from 80% to 66%.

Both groups lost users. That's worth saying plainly: having a success measure didn't stop the drop-off. But the two groups started in nearly the same place, and by month three the pilots without a measure were at 41% weekly active use against 66% for pilots with one.

Month three is also where the decision lands. Northfield and Halvorsen are different studies with different populations, so I wouldn't stitch their numbers together. The timing still lines up: the point where weekly use has slid furthest in unmeasured pilots is about when the median pilot in Halvorsen's group faces its renewal call.

Why would a success measure keep people using a tool? The survey doesn't say, and I'd be guessing if I claimed to know. My read from running these things is that a measure gives a team a reason to keep trying the assistant on real work and to talk about where it helped. Without one, the assistant is an optional extra, and optional extras lose to deadlines. That's my interpretation, and the survey doesn't test it.

## Teams that measured changed work renewed

The sharpest numbers in the Halvorsen report are about renewal. Of the 32 companies, 9 tracked any change in cycle time or review load during the pilot. All 9 renewed. Of the 23 that tracked only seat activation, 11 renewed.

Look at the second half first. 11 of 23 companies renewed with nothing but activation data, so activation-only pilots don't always die. They go either way, and fewer than half of them survived. Whatever decided those 23 cases, the pilots' own data couldn't have, because it didn't answer the question the budget holder was asking. The outcome rested on something else: a sponsor's enthusiasm, say, or how tight the budget was that quarter. Those are my examples, not Halvorsen's, but the point stands that the pilot evidence wasn't what tipped it.

Now the first half, with a caution attached. 9 is a small group, and 9 out of 9 is a result that invites overreading. It fits the idea that measuring changed work helps the renewal case. It also fits the idea that the kind of organisation that sets up cycle-time tracking is the kind that commits to its tools. Halvorsen's data come from interviews with 32 companies, not a controlled trial, and the report can't separate those two explanations.

I still take the lesson, because the mechanism is plain. When the CFO asks what changed, those 9 companies had something to show. The other 23 had a usage chart.

Notice how low the bar was. Halvorsen counted companies that tracked any change in cycle time or review load. That's a before-and-after on one or two numbers rather than a full engineering metrics programme.

## One team picked a number in week one

A director at a fintech ran a pilot across two teams. In week one, one of those teams agreed to track review turnaround. The other team didn't pick a measure.

When renewal came, the first team's numbers made the case. The second team's numbers didn't exist.

Same company, same pilot. The difference came down to a decision made in the first week, by one team, about one number. Review turnaround is a modest choice. It doesn't capture everything an assistant might change, and someone could fairly argue it's the wrong measure for a tool that mostly helps with writing code. But it was agreed early, it could be measured, and it tracks something both authors and reviewers notice. That was enough to give the director a slide the logistics platform lead didn't have.

The part of this story I'd underline is the second team. They used the same tool over the same period, and whatever happened to their work is now invisible. Maybe it got better. Maybe it didn't change. Nobody can say, so their experience contributed nothing to the decision. If you run a multi-team pilot, that's the realistic cost of letting each team decide later: some of your pilot simply won't count.

## The strongest case for stalling

There's a fair objection to everything above. Maybe pilots stall because, for a lot of teams, the assistant doesn't change the work much, and measuring would only confirm it.

A November 2025 Ostrava University study, "Assistant use and review latency," looked at 400 pull requests and found no measurable change in review time with assistant use. If review time is the measure you pick and the effect isn't there, then a stalled pilot may be the correct outcome, reached slowly. Some teams are right to stall.

I take this seriously, and it should change how you read Halvorsen's 9 out of 9. Measuring changed work doesn't guarantee renewal, and it shouldn't. If the fintech team's review turnaround had stayed flat, their numbers would have made the case against renewing just as clearly. A measure is a way to get an answer, not a way to get a yes.

The Ostrava result also has limits. It's one study of 400 pull requests, and review time is one measure among several. It shows that on that measure, in that sample, nothing measurable moved. It doesn't show that assistants change nothing anywhere. It's a reason to pick your measure carefully and to expect that the first one you choose might come back flat.

Look at what the objection actually leaves standing, though. A null result like Ostrava's is evidence. A 92% activation chart isn't. A team that stalls after measuring review time and finding no change has made a decision it can defend to the CFO and revisit later with a different tool or a different measure. A team that stalls after measuring nothing has run out the clock. The counterargument supports measuring work. It just removes the assumption that measuring will make the tool look good.

## What to set up before access goes out

None of this needs a data team. It needs a few decisions made before day one, and an owner for each.

**Agree one work measure in week one, and write down who owns it.** Review turnaround, cycle time or review load are all reasonable starting points. Halvorsen counted any change in cycle time or review load; the fintech team used review turnaround. Pick the one your code review tool already records, so the data is there without new instrumentation.

**Take the baseline before anyone gets a seat.** A month of pre-pilot data on your chosen measure is what turns a number into a comparison. If access has already gone out, use the teams that haven't been onboarded yet as the comparison and say so in the report.

**Put the renewal date in the calendar on day one and plan backwards from it.** The median pilot in Halvorsen's group ran 94 days. If your procurement cycle is similar, your last useful data point is a couple of weeks before that, because someone has to write it up.

**Report weekly active use, not activation, from month two onward.** Northfield's month-three numbers, 41% for pilots with no success measure and 66% for pilots with one, are the drop to watch for. If your weekly use is sliding, find out why while there's still time to change how teams are using the tool.

**Decide in advance what a flat result means.** Given Ostrava's finding on review time, agree before the pilot starts what you'll do if your measure doesn't move: end the pilot, extend it with a second measure, or try a different tool. Writing that down early stops a null result from turning into an argument about whether the measure was fair.

Then do one last check before the meeting. Put the first slide you plan to show at day 90 next to the CFO's question from the logistics company: what changed? If the slide is an activation chart, you're in that platform lead's position, and you have until your renewal date to build something that answers the question.
