# EnvyControl prompt templates

These prompts turn the repository rules into reusable task briefs for coding agents. They are intentionally model-agnostic. Before using any template, replace the bracketed task-specific fields, then give the agent access to the repository and the target branch.

Every prompt inherits `AGENTS.md` (Claude Code reads it too, through the `CLAUDE.md` import). It is authoritative when this library and the repository disagree.

## Rules shared by every implementation prompt

Paste this block at the top of an implementation prompt when the receiving agent does not automatically read repository instructions:

```text
Read AGENTS.md first and obey it. Also read docs/CLI_CONTRACT.md,
docs/COMMAND_PERMISSIONS.md, docs/FACTS.md, and docs/FINDINGS.md before changing
behavior.

If Superpowers skills are available, invoke the relevant process skills before
implementation. If they are unavailable, follow the equivalent workflow manually;
do not fabricate skill/tool output.

TDD is mandatory for behavior changes: RED -> GREEN -> REFACTOR. A bug fix starts
with a failing regression test that demonstrates the bug. Do not delete, weaken,
skip, xfail, or blanket-mock a legitimate failing test merely to get green.

Normal tests must be host-safe. Never write to or remove real EnvyControl-managed
paths, never change GPU mode, never change systemd services, and never rebuild the
real initramfs from the developer workstation. Destructive verification is allowed
only in a disposable VM after all three production gates pass:
ENVYCONTROL_SYSTEM_TEST_VM=1, /etc/envycontrol-test-vm exists, and
systemd-detect-virt --vm positively identifies a VM. There is no force-host bypass.
If such a VM is unavailable, report exactly:
NOT EXECUTED — requires disposable VM

Run the applicable pytest suite, 80% branch-coverage gate, Ruff, mypy, and the
configured security/mutation checks. Never lower a threshold to make a change pass.
Do not merge the PR.
```

## Bootstrap or testing-foundation work

```text
Task: improve EnvyControl's development/test foundation without changing user-visible
runtime behavior.

First inventory the current test, coverage, mutation, lint, type, security, hook,
and VM-verification setup. Use characterization tests around existing behavior
before refactoring legacy code. Test filesystem/subprocess boundaries with tmp_path
and recording fakes, not with real /etc, /usr, /lib, /var/cache/envycontrol,
systemctl, hardware probes, or initramfs tools.

Acceptance:
- new/changed development logic has a RED test before implementation;
- ordinary pytest needs no root, NVIDIA GPU, display manager, or initramfs tool;
- `AGENTS.md` stays the single source of truth; `CLAUDE.md` remains the one-line `@AGENTS.md` shim;
- coverage does not fall below the configured 80% floor;
- any destructive verification remains VM-only and fail-closed;
- document verified facts, not assumed results, in docs/FACTS.md.
```

## New CLI feature or flag

```text
Task: implement [CLI feature/flag].

Treat docs/CLI_CONTRACT.md as the public behavior contract. Begin with tests for
argument parsing, valid/invalid combinations, output/exit behavior, root
requirements, and interactions with existing flags. If the feature can cause a
system mutation, update docs/COMMAND_PERMISSIONS.md before completion and keep all
normal tests behind fakes/tmp_path.

RED first: add a focused CLI test that fails because the new behavior does not yet
exist. GREEN with the smallest production change. REFACTOR only while all focused
tests remain green.

Before completion update CLI help/contract/user stories as applicable, run the full
safe verification, and report destructive VM coverage as PASS only if it actually
ran in a gated disposable VM. Otherwise report NOT EXECUTED — requires disposable VM.
```

## New distro or initramfs backend

```text
Task: add support for [distribution/initramfs mechanism].

Read rebuild_initramfs() and docs/COMMAND_PERMISSIONS.md. Do not detect the distro
from the developer machine during tests. Add a table-driven failing test that feeds
controlled path/tool availability and asserts the exact selected command. Cover
precedence against every existing distro branch so the new detector cannot steal
another platform accidentally.

The host-safe tests must record subprocess calls only. Never execute the new
initramfs command on the workstation. Add/update the disposable-VM fixture only if a
real system-flow assertion is needed.

Completion requires pytest, coverage >= 80%, Ruff, mypy, security checks, and the
current mutation policy. Real initramfs execution is NOT EXECUTED — requires
disposable VM unless a gated test VM was actually used.
```

## GPU-mode behavior change

```text
Task: change [integrated/hybrid/nvidia] behavior: [desired behavior].

This is high-risk system behavior. Read graphics_mode_switcher(), cleanup(),
docs/CLI_CONTRACT.md, and docs/COMMAND_PERMISSIONS.md first. Write a failing
recording-fake test that captures the exact file/service/initramfs effects before
editing production code. Include negative assertions for paths or commands that
must not be touched.

Do not run envycontrol --switch, --reset, --reset-sddm, privileged cache mutation,
or a real initramfs rebuild on the workstation. Normal GREEN proof comes from
host-safe tests. If actual filesystem/system verification is needed, use only
scripts/verify/system-vm.sh in a disposable VM satisfying all three gates.

Update command-permission and CLI contracts when observable effects change. Record
VM verification as PASS only from an actual gated VM run; otherwise:
NOT EXECUTED — requires disposable VM.
```

## Bug fix / systematic debugging

```text
Bug: [symptom, error, or regression].

Use systematic debugging before proposing a fix. Reproduce the failure and trace the
concrete data/control path to the root cause. Do not patch a downstream symptom when
the failing boundary can be made explicit.

TDD requirement:
1. add the smallest regression test that fails for the reported reason;
2. run it and capture the RED evidence;
3. implement one minimal fix;
4. rerun the focused test, then the relevant surrounding suite;
5. run full deterministic verification before claiming success.

If reproduction would mutate the host, reproduce with controlled fakes or in the
gated disposable VM. Never use the real workstation as the fallback environment.
Update docs/FINDINGS.md when the root cause is non-obvious and reusable.
```

## Packaging or release change

```text
Task: change [packaging/release concern].

Preserve the current setuptools runtime/package contract unless the task explicitly
approves a migration. Verify setup.py, the envycontrol=envycontrol:main console
entry point, editable installation, import, and envycontrol --version. Development
tooling in pyproject.toml must not silently change packaging semantics.

Start with a failing packaging/contract test where practical. Run a clean editable
install and safe smoke verification. Do not fold unrelated runtime refactors into a
packaging change. Update user-facing README/install docs only for behavior verified
by the resulting package.
```

## Mutation gate rollout or survivor work

```text
Task: improve EnvyControl mutation quality for [scope].

Run mutmut using scripts/run-mutation.sh so the documented memory cgroup is applied.
Use the repository checker; do not calculate a friendlier score manually. Killed and
survived mutants determine the trusted score; timeout/no-coverage states are
reported separately and never counted as killed.

For each meaningful survivor, add or strengthen a behavioral test first. Avoid
asserting implementation trivia purely to kill mutants. Do not lower the 60%
absolute blocking floor or any higher ratcheted threshold. If the current measured
baseline is below 60%, keep the workflow explicitly advisory and document the real
score/debt until tests raise it to the floor.
```

## Reuse-first audit

```text
Task: review [proposed change] for reusable existing implementation before adding new
code.

Search the repository for existing parsing, filesystem, subprocess, cache,
configuration-template, and test-fixture behavior that already expresses the needed
contract. Prefer a small extension of a proven boundary over a parallel helper with
slightly different semantics.

Do not refactor merely for aesthetic uniformity. Characterize reused legacy behavior
with tests first. Record a concise rationale if duplication is intentionally kept
because merging the paths would increase system risk or alter compatibility.
```

## Debugging + agent orchestration rollout

```text
Task: investigate [multi-part problem] with agent assistance.

One implementation agent owns code changes at a time. Independent read-only review
or investigation may happen in parallel, but do not let multiple agents edit the
same behavior concurrently. Give every agent the same CLI/system contracts and
host-safety invariant.

Require each investigation to return evidence: reproducer, relevant symbols/files,
root-cause hypothesis, commands/tests run, and unresolved uncertainty. Integrate only
findings that can be reproduced or directly verified. Use tests to arbitrate
conflicting proposals, not agent confidence.
```

## Agentic PR verification

```text
Task: verify the current EnvyControl PR as a reviewer, not as its implementer.

Read the PR diff plus AGENTS.md, docs/CLI_CONTRACT.md,
docs/COMMAND_PERMISSIONS.md, docs/FACTS.md, and docs/FINDINGS.md. Run
scripts/verify/verify-pr.sh for safe deterministic checks. Review changed behavior
for missing regression tests, unintended root/system effects, contract drift,
coverage erosion, unsafe subprocess/filesystem access, and attempts to weaken gates.

Run mutation according to the current measured policy. Treat timeouts/no-coverage
separately from killed mutants. Run the Security workflow/checks.

For destructive system scenarios, use scripts/verify/system-vm.sh only when already
inside a disposable VM satisfying the three production gates. Otherwise record:
NOT EXECUTED — requires disposable VM

Return findings ordered by severity with file/symbol evidence. Do not merge the PR.
```

## Disposable-VM system verification

```text
Task: perform EnvyControl destructive system verification in an already-provisioned
disposable Linux VM.

Before doing anything else, confirm the VM is expendable/snapshotted. The repository
guard must independently confirm ENVYCONTROL_SYSTEM_TEST_VM=1,
/etc/envycontrol-test-vm, and systemd-detect-virt --vm. Do not modify the guard or
create a bypass to make the environment qualify.

Run scripts/verify/system-vm.sh exactly as documented. Capture every PASS/FAIL phase
and discard/revert the VM after the run. If any gate refuses execution, stop and
report that refusal; never move the test to a workstation or bare-metal machine.
```

## Reporting template

Use this concise shape after implementation or verification:

```text
Scope:
- [what changed/was verified]

Evidence:
- tests: [command/result]
- coverage: [actual percentage]
- Ruff/mypy: [result]
- mutation: [killed/survived/timeout/no-coverage + trusted score/policy]
- security: [result]
- packaging/smoke: [result]
- destructive VM verification: [PASS with environment evidence | NOT EXECUTED — requires disposable VM]

Known limitations:
- [real remaining limitations only]

Merge status:
- not merged; human decision required
```
