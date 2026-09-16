# EnvyControl — Agent Guide

EnvyControl is a Python CLI for switching NVIDIA Optimus graphics modes on Linux. It changes machine-global graphics configuration, services and initramfs state, so development must treat host safety as a hard invariant.

## Start here

- Read this file, `docs/CLI_CONTRACT.md`, `docs/COMMAND_PERMISSIONS.md`, `docs/FACTS.md` and `docs/FINDINGS.md` before changing behavior.
- **Never perform destructive EnvyControl verification on the developer host.** Any test that can change GPU mode, kernel-module configuration, udev, Xorg, display-manager configuration, systemd services, initramfs, `/etc`, `/usr` or `/var/cache/envycontrol` runs only in a disposable VM created for EnvyControl testing. If no valid disposable VM is available, report destructive verification as **`NOT EXECUTED`**. The real host is never a fallback.
- Search before writing. This is a compact codebase; read `envycontrol.py`, existing tests and scripts before creating a second implementation of the same behavior.
- Read `docs/FINDINGS.md` before debugging or changing build/test tooling. Add a finding only when it is genuinely non-obvious and not derivable from code.
- Read and update `docs/FACTS.md` for verified facts that a fresh agent would otherwise have to rediscover.
- `docs/COMMAND_PERMISSIONS.md` is authoritative for command privilege and side-effect boundaries. Update it in the same change that changes a CLI operation or system side effect.
- If Graphify is available, run it at session start and update it after structural changes. If it is unavailable, inspect the repository directly and state that Graphify was unavailable; never invent graph output.

## Safety invariant: disposable VM only

This rule overrides convenience, speed and confidence in cleanup.

Anything capable of changing GPU mode, kernel-module configuration, udev, Xorg, a display manager, systemd services, initramfs, `/etc`, `/usr`, `/var/cache/envycontrol` or any other machine-global state **MUST run only inside a disposable virtual machine provisioned for EnvyControl testing**.

A destructive system-test script may proceed only when all of these gates pass:

1. `ENVYCONTROL_SYSTEM_TEST_VM=1` is set explicitly.
2. `/etc/envycontrol-test-vm` exists as a regular file in the disposable image.
3. `systemd-detect-virt --vm` exits successfully and reports a non-empty virtualization type other than `none`.

Missing or ambiguous evidence means abort before mutation. There is no `--force-host`, `--i-know-what-im-doing`, environment bypass or equivalent escape hatch. If the VM is unavailable, the result is **`NOT EXECUTED`**, never a host run.

Normal unit/integration tests must use controlled fakes, monkeypatching and temporary paths. They must not require root, a real NVIDIA GPU, a real display manager or a real initramfs tool.

## Project architecture

The runtime intentionally remains small:

- `envycontrol.py` — CLI, graphics-mode logic, system detection, config generation, cache adapter and initramfs selection.
- `setup.py` — setuptools metadata and `envycontrol=envycontrol:main` console entry point.
- `flake.nix` — Nix package/dev-shell definition.
- `tests/` — host-safe pytest suite; dangerous boundaries are blocked by default.
- `scripts/verify/` — safe smoke checks plus VM-only system verification.
- `docs/` — observable CLI contract, command side effects and shared agent knowledge.

Do not split or redesign the runtime merely because a larger architecture is fashionable. Refactors need a concrete behavioral reason and regression coverage.

## CLI and system boundaries

The supported modes are `integrated`, `hybrid` and `nvidia`. Supported display-manager overrides are `gdm`, `gdm3`, `sddm` and `lightdm`. RTD3 values are `0`, `1`, `2`, `3`.

Treat these as dangerous boundaries unless a focused test replaces them:

- filesystem writes/removals below `/etc`, `/usr` and `/var/cache/envycontrol`;
- `systemctl` enable/disable;
- `dracut`, `dracut-rebuild`, `mkinitcpio`, `update-initramfs`, `rpm-ostree`, `make-initrd`;
- `systemd-inhibit` around initramfs rebuilding;
- `chmod` on generated display-manager scripts;
- `lspci` and `xrandr` as hardware/environment discovery inputs.

The exact current impact of each CLI operation lives in `docs/COMMAND_PERMISSIONS.md`.

## Superpowers workflow and mode switches

When Superpowers skills are available, use them before ad-hoc process:

- feature/creative work: `brainstorming` → approved spec → `writing-plans` → approved plan → implementation;
- implementation: `test-driven-development` before production code;
- bugs: `systematic-debugging` before proposing a fix;
- completion: `verification-before-completion` and code review before declaring done.

If a named skill is unavailable in the current agent, follow the equivalent workflow manually and state that the skill was unavailable. Never fabricate a skill result.

Modes:

- **lite mode** — user explicitly disables Superpowers until they say `normal mode`.
- **normal mode** — default; at most one implementation agent writes at a time. A read-only reviewer may overlap when it cannot race on shared mutable state.
- **modo desatendido** — reasonable decisions may be made without waiting, and feature branches/PRs may be pushed/opened if the environment permits. Hard limits remain: never merge, never push directly to the default/protected branch, never force-push.

User instructions outrank skills. This file defines project constraints that skills must respect.

## Heavy jobs and memory cgroup

Full coverage, mutation testing and other long/parallel jobs run under a kernel memory ceiling:

```bash
systemd-run --user --scope --quiet \
  -p MemoryHigh=5G -p MemoryMax=6G -p MemorySwapMax=0 -- <command>
```

Cap the tool's own worker concurrency too. Verify the real worker is inside the cgroup; do not assume a wrapper constrains an external daemon. Never raise the 6 GB ceiling unless the user explicitly asks.

## Tests and quality

The default automated suite is host-safe. **It must never perform destructive verification on the real system.** If a behavior requires real GPU/system mutation, its automated host test stops at mocked boundaries and the real check runs only in the disposable VM. Without that VM, record **`NOT EXECUTED`**; never use the host as fallback.

Testing layers:

1. unit tests for pure parsing, mode inference, config generation and cache behavior;
2. boundary/integration tests with filesystem/subprocess/privilege boundaries replaced;
3. safe CLI smoke tests for non-destructive entry points such as help/version;
4. destructive system verification only through `scripts/verify/system-vm.sh` after the VM guard passes.

`tests/conftest.py` is a safety control, not an inconvenience. Do not weaken it to make a test easy.

## TDD — mandatory

For every new behavior, bug fix or behavior-changing refactor:

1. **RED** — write one focused failing test describing observable behavior.
2. Run it and confirm it fails for the expected reason.
3. **GREEN** — implement only enough to pass.
4. Re-run the focused test and relevant suite.
5. **REFACTOR** only while green.

A bug fix needs a failing regression first. If the failure cannot be observed at that layer, move the assertion to the layer where it can be observed; for machine-global effects that may mean the disposable VM.

Never delete, skip or weaken a test merely to get green. A test that has never been seen fail is not trusted evidence.

## Coverage gate

Use branch coverage. The project floor is **80%** for the measured executable scope; critical pure logic targets **90% or higher**. Do not lower the threshold to ship. Exclusions must be narrow, adjacent to a written project-specific reason, and must not hide testable behavior.

Coverage answers whether code ran, not whether assertions are meaningful; mutation and property tests complement it.

## Property-based testing

Use Hypothesis where invariants are stronger than a list of examples, especially PCI parsing/conversion, stable generated configuration and mode-inference invariants. Strategies must generate valid domain values, not arbitrary shell fragments.

## Mutation gate

Use `mutmut` over meaningful core logic. Measure a real baseline before recording a threshold.

Current measured baseline (2026-09-16, `mutmut 3.8.0`):

- 533 killed, 369 survived, 0 timeouts, 0 skipped, 902 total mutants;
- mutation score: **59.09%**;
- policy: **advisory** because the measured score is below the non-negotiable 60% floor.

Until a fresh mutation run reaches at least **60%**, the next feature or behavior-changing change **MUST NOT be declared complete**. Do not lower the floor, exclude meaningful core logic, or reclassify timeouts/survivors to manufacture a passing score.

- Once blocking, **60% is the absolute floor**.
- The threshold is a ratchet: it can stay or rise, never fall to make a push pass.
- If the measured baseline is below 60%, report the real score/date as advisory and treat reaching 60% as debt before the next feature is considered complete.
- Review `KILLED`, `SURVIVED`, `NO_COVERAGE` and timeouts separately.
- A surviving mutant is fixed by stronger observable assertions, not by recomputing expected values with the implementation's own expression.

Mutation runs are heavy jobs and must use the 6 GB cgroup.

## Real-environment verification

In-process tests cannot prove that EnvyControl changes a real Linux graphics stack correctly. That evidence comes from a disposable test VM.

`./scripts/verify/require-disposable-vm.sh` is the mandatory first gate for destructive verification. `./scripts/verify/system-vm.sh` must call it before any mutation.

The real-environment script verifies externally observable behavior such as exit codes, generated files, service-command logs and mode-query state. Prefer discarding/reverting the VM snapshot after each run over trusting cleanup.

**Never run destructive verification on the developer host.** If the guard cannot positively prove the disposable VM, abort and report **`NOT EXECUTED`**. The host is never a fallback, even when it is a supported Linux distribution or the agent believes cleanup is reversible.

## Debugging discipline

Use instrumentation before repeated ablation. Reproduce first, then locate the causal boundary. If a bug takes more than three expensive reproductions, create a safe shortcut or fixture before a fourth when possible.

A review finding is not a reproduction. Verify it before changing code. `I cannot reproduce this` is a valid result and must not be papered over with a test that starts green.

Expected values in tests must be independently specified. Avoid permissive mocks, self-confirming expectations and assertions that can remain green when the intended behavior is broken.

Environment/performance claims are measurements, not intuition. Record timings only after measuring this repository/environment; never copy timings from templates or another project.

## Agentic PR verification

Every PR should receive an agentic verification verdict before merge. The verifier is advisory and **never merges**.

It must:

1. inspect the diff and relevant spec/contract;
2. run safe host-side lint/tests/coverage;
3. inspect mutation/security results where applicable;
4. use the disposable VM for any scenario that changes machine-global graphics/system state;
5. report CLI output, exit status and expected VM filesystem/service effects;
6. report missing regressions or undocumented behavior;
7. post a readable verdict and wait for the human decision.

**The verifier must never perform destructive testing on the current workstation.** If no valid disposable VM is available, VM-required cases are **`NOT EXECUTED`**. It must not fall back to the host or claim PASS from mocked tests.

## Agent orchestration

`docs/FACTS.md` is shared working memory: verified facts only, with how/date. `docs/FINDINGS.md` is the durable log of non-obvious gotchas not inferable from source.

In normal mode, allow at most one implementation agent at a time. A read-only review may run in parallel when it cannot race. A disposable test VM is an exclusive mutable resource: one worker may mutate a specific VM instance at a time.

Plans should carry contracts and exact names, not unverified code presented as authority. Batch discretionary decisions rather than silently taking product/compatibility decisions away from the user.

## Reuse first

Before creating a helper, script, fixture or abstraction, search `envycontrol.py`, `tests/` and `scripts/` by name and behavior.

- Extend/parameterize behavior that shares a reason to change; do not clone it.
- Two occurrences may remain explicit. At the third true duplicate, extract and migrate all call sites in the same change.
- Do not unify coincidences that will evolve for different reasons.
- Do not add a dependency merely to avoid a small, clear standard-library implementation.
- A deliberate duplicate should be explained in the PR.

## Working rules

- **VM-only destructive verification is non-negotiable.** GPU switching, initramfs rebuilds, systemd/service changes and machine-global file mutations run only in the disposable VM. Without it: **`NOT EXECUTED`**; never host fallback.
- TDD is mandatory for new logic and bug fixes.
- Run full/heavy jobs inside the 6 GB memory cgroup.
- Keep `CLAUDE.md` and `AGENTS.md` byte-for-byte identical; `tests/test_agent_docs.py` enforces it.
- Preserve `setup.py` and the console entry point unless a separately approved packaging migration says otherwise.
- Keep runtime dependencies minimal; test/development tools do not belong in `setup.py` runtime requirements.
- Update `docs/CLI_CONTRACT.md` when observable CLI behavior changes.
- Update `docs/COMMAND_PERMISSIONS.md` in the same change as privilege/side-effect behavior.
- Never invent coverage, mutation, timing, VM or hardware results.
- Commits in English using Conventional Commits.

## Git & GitHub

- Commits and feature branches are allowed when useful.
- Default: do not push unless the user asked for repository changes through an authorized tool or `modo desatendido` explicitly permits feature-branch pushing.
- Never push directly to `main`/default/protected branches.
- Never force-push or use `--force-with-lease`.
- **Never merge** branches or PRs. The user decides merges.
- Branch names: `feat/name`, `fix/description`, `chore/task` when creating new branches.
- Every PR must include a **How to test manually** section with exact safe commands, prerequisites and expected results.
- PR verification must distinguish deterministic PASS from VM-required `NOT EXECUTED`; mocked host tests never substitute for destructive VM evidence.
