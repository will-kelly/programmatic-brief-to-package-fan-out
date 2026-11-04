# Review packet: heroku-alternatives-draft

**1 claims need you.** 0 verified against the docs, 2 corroborated by seed facts only, 3 lint errors. Estimated review time 10.0 minutes (about 16.0 without the checker).

The writer sent no claims ledger, so one was extracted. Check that nothing important is missing from it.

## Decide these

### C1: contradicted

> Render offers a free tier that includes background workers.

Why flagged: matches a known-wrong pattern for F-free-no-workers: Background workers and cron jobs aren't available on the free instance type. (by registry-pattern)

Docs say (free#intro):

> Render offers free instance types for web services, Render Postgres, and Render Key Value, for hobby projects and testing.

- [ ] Correct as written   - [ ] Fix copy   - [ ] Fix docs or registry

## Lint

- **fingerprint** (error): machine-sounding phrase 'robust' — `robust`
- **answer-first** (error): opens with preamble instead of the answer — `When it comes to replacing Heroku, developers have more choices than ever, and p`
- **concede** (error): comparison has no section on when the other option wins. One-sided comparisons read as ads, and answer engines treat them that way.
- **untagged-superlative** (warning): 'Best' with no claim behind it — `# The Best Heroku Alternatives for 2026`
- **untagged-superlative** (warning): 'best' with no claim behind it — `Render is the best Heroku alternative for most teams.`
- **question-headings** (warning): fewer than a third of H2s are phrased as the question a developer would ask
- **sentence-case** (warning): heading isn't sentence case — `The Best Heroku Alternatives for 2026`
- **verified-date** (warning): no last_verified date in front matter
- **targets** (warning): front matter doesn't list target_questions, so the survey can't measure this page

## Corroborated only (spot-check one)

- C2: Render supports Docker deploys from a Dockerfile or a prebuilt image. (docker#overview)
- C3: Render gives every pull request a preview environment with its own copy of your databases. (preview-environments#overview)

## When you're done

```bash
cf review done <run-dir> --minutes <n> --corrections <n>
```

Every correction you make that the checker passed becomes an eval case, so the checker learns what it missed.
