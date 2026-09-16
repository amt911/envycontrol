# EnvyControl agentic development foundation — design

## Goal

Adapt the complete useful intent of the temporary `claude-md/` template tree into EnvyControl itself, then remove `claude-md/` entirely. The result must give future LLMs an executable, project-specific development workflow: mandatory TDD, coverage and mutation gates, safe system-boundary testing, Python-native quality tooling, durable project knowledge, and PR verification rules.

The adaptation is intentionally native to EnvyControl. Web/mobile-specific mechanics from the template are not copied literally; their engineering purpose is translated to this Python CLI that changes Linux graphics configuration, system services and initramfs state.

## Non-goals

- Do not redesign or substantially refactor `envycontrol.py` in this change.
- Do not change the observable GPU-switching behavior merely to make testing easier.
- Do not introduce Node, pnpm, Husky, Playwright, Maestro, web design-system conventions or backend endpoint concepts into this Python CLI.
- Do not run destructive system tests on the developer workstation.
- Do not make mutation scores, coverage numbers, timings or environment claims up. Baselines are measured before hard numbers are committed.

## Safety invariant: destructive verification runs only in a disposable VM

This is the highest-priority rule in the project.

**Anything capable of changing GPU mode, kernel-module configuration, udev, Xorg, a display manager, systemd services, the initramfs, `/etc`, `/usr`, `/var/cache/envycontrol`, or other machine-global state MUST run only inside a disposable virtual machine created for EnvyControl testing. It must never run on the developer's real host, even if the host is a supported Linux system, even if the command would normally be safe, and even if an agent believes it can restore the state afterwards.**

Normal unit/integration tests must replace every dangerous boundary with controlled test doubles and temporary paths. They may not require a real NVIDIA GPU, root access, a real display manager, or a real initramfs implementation.

System-test scripts must fail closed. A destructive system test may proceed only when all of the following independent gates pass:

1. An explicit opt-in environment variable, e.g. `ENVYCONTROL_SYSTEM_TEST_VM=1`, is present.
2. A sentinel provisioned only in the disposable test image, e.g. `/etc/envycontrol-test-vm`, exists.
3. `systemd-detect-virt --vm` (or an equivalent verified VM check when unavailable) confirms virtualization rather than bare metal.
4. The verification script prints the detected environment and aborts before making changes when any gate is missing or ambiguous.

A caller cannot bypass these checks with a convenience flag. There is no `--force-host`, `--i-know-what-im-doing`, or equivalent escape hatch. If a platform cannot prove it is the disposable VM, destructive verification does not run.

Agentic PR verification obeys the same invariant. An agent may inspect code and run safe host tests, but any command that can mutate machine-global graphics/system state must be delegated to the disposable VM. The agent must never "try it carefully" on the host.

## Canonical agent instructions

Create a project-specific root `CLAUDE.md` and make root `AGENTS.md` a byte-for-byte copy. A test must enforce that the two files stay identical.

The guide will preserve and adapt the governance from `claude-md/docs/starter-kit/CLAUDE.template.md`:

- session start/read-first rules;
- graphify guidance when available;
- Superpowers workflow and mode switches;
- mandatory TDD;
- coverage and mutation quality gates;
- real-environment verification;
- debugging loop discipline;
- agent orchestration and shared facts;
- reuse-first rules;
- memory-cgroup protection for heavy jobs;
- Git/GitHub rules, including never merging and default no-push behavior;
- mandatory PR manual test plans and agentic verification.

The stack/preset sections will be rewritten for the actual project: one Python CLI module, setuptools packaging, Linux/systemd/initramfs boundaries, and the current supported GPU/display-manager behaviors.

`CLAUDE.md` must state the VM-only safety invariant prominently in Start here, testing rules, real-environment verification, working rules, and PR verification so a future agent cannot miss it by reading only one section.

## Documentation mapping

The temporary template files map as follows.

| Temporary source | EnvyControl destination / adaptation |
| --- | --- |
| `claude-md/CLAUDE.md` | Fold useful repo-governance conventions into root `CLAUDE.md`; discard meta-repo-only wording. |
| `claude-md/README.md` | Do not replace the product README. Preserve only relevant development concepts through the new project docs. |
| `claude-md/.markdownlint.jsonc` | Move/adapt to root if still useful for the Markdown documentation added here. |
| `claude-md/.github/dependabot.yml` | Replace with root Dependabot config for Python/dev tooling and GitHub Actions. |
| `claude-md/.github/workflows/ci.yml` | Replace with EnvyControl Python CI rather than copying docs-only CI. |
| `docs/starter-kit/CLAUDE.template.md` | Project-specific root `CLAUDE.md` plus identical `AGENTS.md`. |
| `DESIGN-SYSTEM.template.md` | `docs/CLI_CONTRACT.md`: user-visible CLI contract, messages, exit behavior, reboot expectations and compatibility rules. |
| `ENDPOINT_PERMISSIONS.template.md` | `docs/COMMAND_PERMISSIONS.md`: each CLI operation's root requirement, reads/writes/removals, services and external commands. |
| `FACTS.template.md` | `docs/FACTS.md`, seeded only with verified repository facts and their verification source. |
| `FINDINGS.template.md` | `docs/FINDINGS.md`, initially documenting only genuinely non-obvious environment/tooling gotchas discovered during this work. |
| `USER-STORIES.template.md` | `docs/USER_STORIES.md`, describing existing user journeys and acceptance behavior for integrated/hybrid/NVIDIA switching, reset, query and cache flows. |
| `starter-kit/README.md` | Its bootstrap intent is absorbed into the project-specific workflow docs; no generic starter kit remains. |
| `PROMPT_TEMPLATES_WEB.md` | `docs/PROMPT_TEMPLATES.md`, rewritten for EnvyControl tasks: flags/features, distro/initramfs support, bugs, packaging, mutation rollout, reuse, debugging/orchestration and PR verification. |

After all adapted destinations exist and cross-references resolve, delete the entire `claude-md/` directory. It must not remain as a second source of truth.

## Python testing architecture

Use a Python-native development toolchain centred on `pytest`.

### Test layers

1. **Unit tests** — pure or tightly scoped behavior: PCI parsing, vendor detection, mode inference, generated configuration strings, cache object behavior, argument parsing and command selection.
2. **Boundary/integration tests** — exercise EnvyControl code while replacing filesystem, subprocess and privilege boundaries with explicit fakes/monkeypatches. All writes use `tmp_path` or a controlled virtual filesystem abstraction.
3. **Safe CLI smoke tests** — subprocess-level checks of non-destructive behavior such as `--help`, `--version` and packaging/entry-point behavior. They must not mutate system graphics state.
4. **Destructive system verification** — separate scripts that run only in the disposable VM under the safety invariant above.

### Host safety guard

`tests/conftest.py` will install fail-closed guards for dangerous operations during normal pytest runs. Tests must explicitly replace a dangerous boundary before exercising code that reaches it. At minimum the guard must prevent accidental real execution/writes involving:

- `systemctl`;
- `dracut`, `dracut-rebuild`, `mkinitcpio`, `update-initramfs`, `rpm-ostree`, `make-initrd`;
- writes/removals under EnvyControl's real `/etc`, `/usr` and `/var/cache/envycontrol` paths;
- real chmod/service/display-manager mutations triggered by the application.

The guard itself gets regression tests: one test proves a dangerous real command is rejected, and another proves an explicitly mocked equivalent can be exercised safely.

### TDD

New logic and every bug fix follow mandatory Red → Green → Refactor:

1. Write a focused failing test describing the intended observable behavior.
2. Run that test and capture that it fails for the expected reason.
3. Implement the minimum change.
4. Run the focused test green.
5. Run the relevant suite and refactor only while green.

A bug fix without a demonstrated red regression first is incomplete unless the failure is structurally unobservable at that test layer; in that case the assertion must move to the layer where it is observable, including the disposable VM when necessary.

## Coverage, properties and mutation testing

Use `pytest-cov`/coverage.py with an initial project gate of at least 80% statement and branch coverage for the measured executable scope. Critical pure logic should target at least 90%. Exclusions require an inline, project-specific justification; lowering the threshold to get green is forbidden.

Use Hypothesis where invariants are stronger than hand-picked examples, especially parsing and conversion behavior such as PCI address handling and stable configuration generation.

Use `mutmut` for mutation testing over a deliberately meaningful core-logic scope. The policy from the template is retained:

- 60% is the absolute floor once the gate becomes blocking;
- the threshold is a ratchet and only moves upward;
- measure the real baseline before writing a number;
- if the initial score is below 60%, CI reports it advisory with score/date and the debt to reach 60 before the next feature;
- distinguish surviving mutants from uncovered mutants before drawing conclusions;
- expected values must not be recomputed with the implementation expression.

Mutation testing is a heavy job and must run inside the documented 6 GB memory cgroup with tool concurrency capped as appropriate.

## Static quality and dependency checks

Centralize development configuration in `pyproject.toml` without removing or breaking the current setuptools entry point in `setup.py`.

Adopt:

- Ruff for fast lint/static checks;
- mypy progressively, without forcing a large unrelated type-refactor in this branch;
- Semgrep for SAST/secrets scanning;
- pip-audit for Python dependency vulnerability checks;
- vulture as an initially advisory dead-code report;
- markdownlint for the new Markdown corpus when useful.

Runtime dependencies remain minimal. Development tooling is clearly separated from the installable EnvyControl runtime.

## Hooks

Use `pre-commit`, not Husky.

- **pre-commit hook:** cheap deterministic checks such as Ruff, whitespace/config validation, Markdown checks and focused static validation.
- **pre-push hook:** full pytest suite + coverage gate, followed by mutation testing as the final/slowest step when the measured gate is ready to be blocking.

No hook may launch destructive GPU/system verification on the host. The pre-push hook may validate the VM verification scripts and run safe tests around their fail-closed guards, but it must never perform a real mode switch, initramfs rebuild or service mutation.

## GitHub Actions

Use separate workflows with non-overlapping responsibilities:

- `ci.yml`: Python setup, lint/static checks, unit/integration tests and coverage;
- `mutation.yml`: mutation report for PRs against the default branch, initially advisory until the measured threshold policy says it can block;
- `security.yml`: dependency audit plus SAST/secrets checks;
- Dependabot: GitHub Actions and the chosen Python dependency representation.

Destructive VM system tests are not silently run on ordinary GitHub-hosted runners. They require an explicitly provisioned VM-capable test environment that satisfies the same three environment gates. Until such a runner is deliberately configured, the destructive verification remains an explicit local/dedicated-VM step and is documented as such.

## Real-environment verification

Create `scripts/verify/` with safe smoke verification and a separate destructive system-test entry point.

The destructive script must:

- execute only after all VM gates pass;
- print the virtualization evidence before mutation;
- use a disposable snapshot/image intended for EnvyControl;
- exercise externally observable results: exit codes, generated files, service state and mode query behavior;
- restore or discard VM state after the run; discarding the disposable VM/snapshot is preferred over trusting cleanup;
- stop on the first failed invariant and return non-zero;
- never contain a host override.

Testing against the developer's actual Arch installation is explicitly forbidden by project policy. The fact that the developer machine is a supported Linux environment does not make it a test target.

## Agentic PR verification

Every PR must receive an agentic verification verdict before merge, but the verifier never merges.

For EnvyControl the verifier will:

1. inspect the PR diff and relevant spec cases;
2. run safe host-side lint/tests/coverage as appropriate;
3. inspect mutation/security results where applicable;
4. use the dedicated disposable VM for any behavior that changes global graphics/system state;
5. verify CLI output, exit status and expected VM filesystem/service effects;
6. report missing regression tests or undocumented behavior;
7. post a readable PR comment and wait for the human decision.

The verifier is advisory; deterministic tests are the hard evidence. If no disposable VM is available, the agent reports destructive verification as **not executed**. It does not substitute the real host.

## CLI contract and command permissions

`docs/CLI_CONTRACT.md` becomes the observable compatibility reference. It records supported flags/modes, user-visible output expectations, reboot semantics, errors and compatibility constraints so a future refactor cannot silently change the CLI.

`docs/COMMAND_PERMISSIONS.md` is the authoritative system-impact table. Each command/operation records:

- whether root is required;
- files/directories read, written or removed;
- services enabled/disabled;
- external commands invoked;
- whether it rebuilds initramfs;
- whether a real-environment test therefore requires the disposable VM.

The table is updated in the same change as any CLI operation/system side effect.

## Debugging and agent orchestration

Retain the template's instrumentation-first debugging discipline without copying measurements from another project. Timings are recorded only after being measured here.

`docs/FACTS.md` stores verified, rediscoverable repository/system facts. `docs/FINDINGS.md` stores durable non-obvious gotchas that are not apparent from reading the code.

Normal mode permits at most one implementation agent at a time; read-only review may overlap when it cannot race on shared mutable state. The disposable system-test VM is an exclusive resource: only one implementation/verification worker may mutate a given VM instance at once.

## Reuse-first rule

Because the project is currently compact, reuse means first searching `envycontrol.py`, tests and scripts for existing behavior before adding another helper or command abstraction. Extend or parameterize behavior that shares a reason to change; do not abstract mere coincidences. A third true duplicate is the trigger to extract, with all call sites migrated and old copies removed in the same change.

## README and packaging

Keep the current product `README.md` focused on EnvyControl users. Add only a concise development/contributing pointer if necessary; do not replace it with template-repo documentation.

Keep `setup.py` functional and preserve the existing console-script entry point. Introducing `pyproject.toml` for tooling/configuration must not silently change installation semantics in this branch.

## Implementation sequence

After this design is approved, the implementation plan should stage work so each slice is independently reviewable:

1. Establish project docs and canonical agent rules (`CLAUDE.md`/`AGENTS.md`).
2. Add safe pytest infrastructure and host-protection tests before expanding coverage.
3. Add behavioral tests around existing code without functional rewrites.
4. Add coverage/Hypothesis/static tooling.
5. Measure and integrate mutation testing.
6. Add hooks and CI/security workflows.
7. Add VM-only verification scripts and their fail-closed host tests.
8. Adapt the prompt library and remaining docs.
9. Delete `claude-md/` completely.
10. Run final consistency/quality verification and review the full diff.

## Acceptance cases

The change is complete only when all of these are true:

- Root `CLAUDE.md` is specific to EnvyControl and contains no web-stack placeholders.
- Root `AGENTS.md` exists and is byte-for-byte identical to `CLAUDE.md`, enforced by a test.
- TDD is both documented and executable through pytest.
- A normal pytest run cannot execute real system-mutating EnvyControl boundaries.
- A regression test demonstrates that an attempted dangerous host command is blocked.
- Safe tests use temporary state and do not require root/NVIDIA/systemd/initramfs.
- Coverage is measured and enforced according to the documented gate.
- Mutation testing has a measured baseline and follows the 60%-floor ratchet policy without inventing a score.
- Hypothesis is used for at least one meaningful invariant suitable to this codebase.
- Python lint/static/security/dependency tooling has real runnable commands.
- `docs/CLI_CONTRACT.md`, `docs/COMMAND_PERMISSIONS.md`, `docs/FACTS.md`, `docs/FINDINGS.md`, `docs/USER_STORIES.md` and `docs/PROMPT_TEMPLATES.md` exist and are EnvyControl-specific.
- CI and hooks never perform destructive GPU/system operations on the host.
- Destructive system verification refuses to run unless explicit opt-in + VM sentinel + virtualization detection all pass.
- There is no override allowing destructive tests on bare metal.
- Agentic PR verification explicitly treats the disposable VM as the only valid target for system mutation; lack of a VM yields "not executed", never fallback to the host.
- `setup.py` and the console entry point remain functional.
- The product README remains a product README.
- The complete `claude-md/` directory is removed after adaptation.
- No unresolved template placeholders or stale references to the removed `claude-md/` tree remain.

## Human-control boundary

The workflow improves rigor but does not transfer product authority to an agent. Acceptance criteria and consequential behavior changes remain human-reviewed. Agents may create commits and branches under the documented Git rules, but never merge; destructive verification has no host fallback; and ambiguity around system safety resolves to **do not run**.
