# FINDINGS — EnvyControl

Durable log for non-obvious build, test and environment gotchas that are not apparent from reading the repository. Read this before debugging or changing build/test tooling.

## Entry format

Each finding records symptom, cause, fix/workaround, why it was non-obvious, date and area. Do not copy anecdotes or timings from another project.

## Findings

### `xrandr` failure could escape as `UnboundLocalError`

- **Symptom:** a failed AMD-provider `xrandr` probe could leave the later match variable undefined instead of cleanly reporting no provider.
- **Cause:** the command-error branch logged the failure but continued into code that expected a successful regex result.
- **Fix:** a RED regression test reproduced the failure; the implementation now returns `None` immediately when `xrandr` fails.
- **Why non-obvious:** the happy path and missing-command path were both reasonable, while only a command that exists and exits unsuccessfully exposed the undefined local.
- **Date/area:** 2026-09-16, detection/runtime regression.

### `mutmut` plus root `systemd-run` changes sandbox ownership

- **Symptom:** mutation execution completed all generated mutants, but `mutmut export-cicd-stats` failed with a permission error afterwards.
- **Cause:** CI runs the memory-capped mutation process through `sudo systemd-run`; `mutmut` therefore creates/updates `mutants/` as root while the later export runs as the unprivileged runner.
- **Fix:** after a successful mutation run, CI restores ownership of `mutants/` to the current runner before exporting results. Local runs do not add this `sudo` path.
- **Why non-obvious:** the mutation process itself succeeded; the failure happened only in the post-run export boundary.
- **Date/area:** 2026-09-16, mutation infrastructure.

### Mutation baseline is just below the blocking floor

- **Symptom:** the first reliable full mutation run produced 533 killed and 369 survived mutants out of 902 total, for **59.09%**.
- **Cause:** the newly bootstrapped characterization suite does not yet kill enough core-logic mutants to meet the mandatory 60% floor.
- **Fix/workaround:** keep mutation advisory exactly as the approved plan requires; do not lower the floor. The next feature or behavior-changing change cannot be declared complete until a fresh run reaches at least 60%.
- **Why non-obvious:** coverage is already 85.15%, showing why line/branch execution alone does not establish assertion strength.
- **Date/area:** 2026-09-16, test quality/mutation.
