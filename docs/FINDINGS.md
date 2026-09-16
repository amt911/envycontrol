# FINDINGS — EnvyControl

Durable log for non-obvious build, test and environment gotchas that are not apparent from reading the repository. Read this before debugging or changing boot/build/test tooling.

## Findings

### `xrandr` failure could escape as `UnboundLocalError`

- **Symptom:** a failed AMD-provider `xrandr` probe could leave the later match variable undefined instead of cleanly reporting no provider.
- **Cause:** the command-error branch logged the failure but continued into code that expected a successful regex result.
- **Fix:** a RED regression test reproduced the failure; the implementation now returns `None` immediately when `xrandr` fails.
- **Date/area:** 2026-09-16, detection/runtime regression.

### Installed boot generators are not proof that they are active

- **Symptom:** on Arch, both `dracut` and `mkinitcpio` can remain installed even though only one is actually integrated into package/kernel updates.
- **Cause:** binary presence is weaker evidence than active pacman hooks, explicit config or generated-artifact evidence.
- **Fix:** boot detection uses ranked evidence. In particular, active dracut integration beats mkinitcpio being merely installed, so EnvyControl does not run both.
- **Why non-obvious:** package presence is convenient to detect but can select the wrong rebuild mechanism after a user migrates generators without uninstalling the old package.
- **Date/area:** 2026-09-16, Arch boot-generator detection.

### Preflight must happen before the cache adapter, not only before GPU writes

- **Symptom:** an ambiguous/unsupported boot setup could fail before `cleanup()` yet still allow `CachedConfig.adapter()` to refresh `/var/cache/envycontrol` first.
- **Cause:** the legacy CLI entered the cache adapter before root/system operation dispatch.
- **Fix:** `--switch` and `--reset` now assert root and resolve one immutable boot plan before constructing/entering the adapter. The same plan is reused after mutation.
- **Why non-obvious:** saying “preflight before system mutation” was too weak because cache refresh is itself a machine-global write.
- **Date/area:** 2026-09-16, CLI/preflight safety boundary.

### Booster regeneration cannot be intercepted with `PATH`

- **Symptom:** a PATH fixture can fake `dracut`, `mkinitcpio`, `kernel-install` and similar commands, but not Booster regeneration.
- **Cause:** Booster's supported rebuild command is the absolute path `/usr/lib/booster/regenerate_images`.
- **Fix/workaround:** unit/integration tests fake the command runner. Real Booster validation is performed only in a purpose-built disposable VM/snapshot and the VM is discarded/reverted afterwards.
- **Why non-obvious:** most other boot tools are resolved through `PATH`, so a fixture-bin strategy looks complete until the absolute Booster command is inspected.
- **Date/area:** 2026-09-16, VM verification.

### `mutmut` plus root `systemd-run` changes sandbox ownership

- **Symptom:** mutation execution completed all generated mutants, but `mutmut export-cicd-stats` failed with a permission error afterwards.
- **Cause:** CI runs the memory-capped mutation process through `sudo systemd-run`; `mutmut` therefore creates/updates `mutants/` as root while the later export runs as the unprivileged runner.
- **Fix:** after a successful mutation run, CI restores ownership of `mutants/` to the current runner before exporting results. Local runs do not add this `sudo` path.
- **Date/area:** 2026-09-16, mutation infrastructure.

### `mutmut` sandbox must contain `setup.py`

- **Symptom:** the first mutation attempt covering both runtime modules failed before measuring mutants because the packaging characterization test could not find `setup.py` inside mutmut's sandbox.
- **Cause:** `also_copy` contained scripts/docs/config but omitted packaging metadata.
- **Fix:** `setup.py` is included in `tool.mutmut.also_copy`.
- **Date/area:** 2026-09-16, mutation infrastructure.

### Two-module mutation gate is now above the blocking floor

- **Result:** the first reliable run covering both `envycontrol.py` and `envycontrol_boot.py` produced **878 killed, 523 survived, 1 no-tests, 0 timeouts, 0 skipped; 1402 total**, with a checker score of **62.67%** against the mandatory **60.00%** floor.
- **Policy:** mutation is now blocking in GitHub Actions and local pre-push verification. Do not lower the threshold or exclude difficult production code to preserve the score; add meaningful tests for survivors instead.
- **Why non-obvious:** the earlier single-module foundation baseline was 59.09%; adding a large new module could easily have reduced test strength, so the fresh combined measurement was required before promotion.
- **Date/area:** 2026-09-16, test quality/mutation.
