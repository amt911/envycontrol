# Boot Rebuild Backends Design

Date: 2026-09-16
Status: approved in chat, awaiting written-spec review
Branch: `feat/boot-rebuild-backends`

## Context

EnvyControl currently decides how to rebuild boot artifacts inside `rebuild_initramfs()` using distribution markers. On Arch Linux the presence of `/etc/arch-release` unconditionally maps to `mkinitcpio -P`, even when the installed system actually uses dracut or Booster. EndeavourOS has a special-case `dracut-rebuild` branch, but plain Arch with dracut is misdetected.

That architecture couples distribution detection, initramfs-generator selection, command execution and `systemd-inhibit` wrapping in one function. It also discovers rebuild capability only after graphics-mode code has already started changing machine-global state.

The result is unsafe and not extensible enough for current Arch boot setups such as dracut, Booster, `kernel-install`, UKIs and Limine integrations.

## Verified external constraints

The design is based on current Arch Linux documentation as of 2026-09-16:

- Arch supports mkinitcpio, dracut and Booster as initramfs generators.
  - https://wiki.archlinux.org/title/Dracut
  - https://wiki.archlinux.org/title/Booster
- The documented dracut all-kernel rebuild command is `dracut -f --regenerate-all`.
- Booster provides `/usr/lib/booster/regenerate_images` to regenerate images for installed kernels.
- `kernel-install` can explicitly configure `layout=`, `initrd_generator=` and `uki_generator=` in `/etc/kernel/install.conf`, and `kernel-install inspect --verbose` can explain resolved defaults.
  - https://wiki.archlinux.org/title/Kernel-install
- `ukify` does not generate an initramfs by itself; it consumes an initramfs produced by another generator.
  - https://wiki.archlinux.org/title/Unified_kernel_image
- Limine has generator-specific automation such as `limine-dracut-support` and `limine-mkinitcpio-hook`; therefore Limine must not be treated as an initramfs generator.
  - https://wiki.archlinux.org/title/Limine

These facts shape the architecture below. The implementation must not collapse initramfs generation, UKI composition and bootloader integration into one interchangeable backend type.

## Goals

1. Correctly support Arch systems using mkinitcpio, dracut or Booster.
2. Preserve existing Debian/Ubuntu, RHEL/SUSE, ALT Linux and rpm-ostree behavior.
3. Model `kernel-install`, UKI generation and Limine integration without conflating them with initramfs generation.
4. Select the active mechanism from real configuration/integration evidence, not distro name alone.
5. Fail closed when configuration is ambiguous or unsupported.
6. Resolve and validate the boot-rebuild plan before EnvyControl mutates system state.
7. Follow SOLID without over-engineering the rest of EnvyControl.
8. Keep every normal automated test host-safe; destructive validation remains disposable-VM-only.
9. Finish with a fresh mutation score of at least 60%, including the new module in mutation scope.

## Non-goals

- Do not migrate the whole application into a Python package in this change.
- Do not automatically edit mkinitcpio `MODULES=()`, dracut `force_drivers`, or Booster `modules_force_load` for NVIDIA in this change.
- Do not invent support for arbitrary custom boot scripts.
- Do not make Limine presence alone trigger a command.
- Do not run a real initramfs rebuild, graphics-mode switch, systemd service change or bootloader mutation on the developer host.
- Do not change the public `envycontrol=envycontrol:main` console entry point.

## Root cause

The current primary defect is not simply “dracut is unsupported”. The root cause is that the implementation asks the wrong question.

Current model:

`distribution marker -> hard-coded rebuild command`

Desired model:

`observed boot configuration -> validated rebuild plan`

On Arch, `/etc/arch-release` is insufficient evidence for mkinitcpio. A system may have mkinitcpio installed while dracut is active, or may use Booster. Therefore distro detection may be a fallback signal, but it must not override stronger configuration evidence.

A secondary defect exists in the same boundary: `systemd-inhibit` is currently composed around the command after selection, and an unknown distribution can conceptually lead to wrapping an empty command. In the new design, inhibition decorates only an already-valid plan.

## Architectural direction

Introduce one focused module, `envycontrol_boot.py`, while preserving `envycontrol.py` as the CLI/runtime entrypoint.

`setup.py` continues to expose `envycontrol=envycontrol:main`, and `py_modules` gains `envycontrol_boot`.

The new module owns boot rebuild resolution. It contains small abstractions with separate responsibilities rather than a single inheritance-heavy hierarchy.

### Core collaborators

#### `SystemProbe`

A read-only interface for observing the host:

- path existence;
- regular-file/symlink information when needed;
- command availability;
- reading text files;
- determining whether an override hook is masked to `/dev/null`;
- optionally running read-only inspection commands such as `kernel-install inspect --verbose` through an injected command boundary.

Production implementation delegates to `os`, `pathlib`, `shutil.which` and a read-only command runner. Tests use a fake probe.

Backends must not directly call global filesystem/process APIs for detection.

#### `CommandRunner`

An execution abstraction responsible only for running a prepared argv vector and returning an execution result.

The production runner preserves current quiet-vs-verbose behavior. A decorator may wrap a valid command with `systemd-inhibit` when available.

Detection and execution remain separate.

#### `DetectionEvidence`

Detection must be explainable. Each backend returns typed evidence rather than an opaque arbitrary score.

Evidence classes, ordered strongest to weakest:

1. `EXPLICIT_CONFIG` — explicit generator selection, for example `initrd_generator=dracut`.
2. `ACTIVE_INTEGRATION` — active pacman/kernel-install integration or equivalent.
3. `GENERATED_ARTIFACT` — artifacts whose naming/layout strongly indicates a generator.
4. `DISTRO_DEFAULT` — a distribution default when no stronger evidence exists.
5. `BINARY_PRESENT` — executable availability only.

The resolver owns precedence. Individual backends do not invent numeric confidence values.

#### `DetectionResult`

Contains:

- backend identifier;
- collected evidence;
- whether the candidate is eligible;
- diagnostic explanation suitable for verbose output.

#### `InitramfsBackend`

A narrow `Protocol` with responsibilities equivalent to:

- `name`;
- `detect(probe) -> DetectionResult`;
- `build_command(probe) -> tuple[str, ...]`.

Backends do not mutate the host during detection or command construction.

Initial implementations:

- `MkinitcpioBackend` -> `mkinitcpio -P`;
- `DracutBackend` -> `dracut -f --regenerate-all`;
- `BoosterBackend` -> `/usr/lib/booster/regenerate_images`;
- `UpdateInitramfsBackend` -> `update-initramfs -u -k all`;
- `RpmOstreeBackend` -> current rpm-ostree initramfs command;
- `MakeInitrdBackend` -> `make-initrd`.

The old EndeavourOS `dracut-rebuild` special case is treated as compatibility evidence/behavior to preserve if required by the installed integration, not as proof that all Arch dracut systems use `dracut-rebuild`.

### `KernelInstallStrategy`

`kernel-install` is orchestration, not an initramfs generator.

When `/etc/kernel/install.conf` explicitly selects a layout/generator, that explicit configuration outranks distro defaults and binary presence.

If the system is demonstrably managed by `kernel-install`, the plan may delegate rebuild orchestration to `kernel-install add-all` rather than separately invoking the selected initramfs generator and UKI tool. The resolver must ensure only one orchestration path executes.

`kernel-install inspect --verbose` may be used as read-only diagnostic evidence, but parsing must be defensive and tested. Explicit config files remain preferred over unstable human-oriented output where possible.

### UKI handling

UKI generation is modeled as an artifact stage, not an `InitramfsBackend`.

Supported cases include:

- mkinitcpio presets that already generate UKIs;
- dracut configurations that already generate UKIs;
- `kernel-install` with `layout=uki` and a resolved `uki_generator` such as `ukify`.

The implementation must not call `ukify` a second time when the selected orchestration path already creates the UKI.

A standalone `UkifyStrategy` is only valid when configuration clearly requires EnvyControl to orchestrate that stage. The first implementation should prefer existing native orchestration (`kernel-install`, mkinitcpio presets, dracut configuration) rather than reconstructing complex UKI commands from guessed paths.

### Limine integration

Limine is a post-generation bootloader integration.

Known integrations may be recognized when their installed/configured automation is explicit, for example generator-specific Limine packages/hooks documented by Arch.

Rules:

- Limine presence alone is not enough to run an update command.
- Known native integration that is already triggered by the selected generator should not be duplicated.
- If EnvyControl can prove the selected pipeline leaves Limine correctly updated, no extra command is added.
- If Limine is detected but the integration is custom/unknown and stale boot entries could result, preflight fails with `UnsupportedBootIntegrationError` before graphics configuration is modified.

Booster plus hand-written Limine scripts is an example of a setup EnvyControl must not guess.

## Resolution algorithm

Resolution happens before any graphics-mode side effects.

High-level order:

1. Detect special immutable/OSTree systems and preserve their explicit path.
2. Inspect explicit `kernel-install` configuration.
3. Gather backend evidence for mkinitcpio, dracut, Booster and distro-specific generators.
4. Suppress candidates whose native integration is explicitly masked/disabled.
5. Resolve the strongest candidate by evidence precedence.
6. If multiple candidates remain equally authoritative, raise an ambiguity error.
7. Resolve UKI/orchestration requirements.
8. Resolve bootloader integration requirements.
9. Produce an immutable `BootRebuildPlan`.
10. Only after a valid plan exists may graphics-mode mutation start.
11. Execute the prepared plan after configuration changes are written.

No detection step may mutate machine-global state.

## Arch-specific evidence

### dracut

Useful evidence includes:

- explicit `kernel-install` generator selection;
- active dracut pacman integration/hooks;
- dracut configuration under `/etc/dracut.conf` or `/etc/dracut.conf.d/`;
- mkinitcpio hooks explicitly masked to `/dev/null` as supporting evidence;
- generated dracut artifacts where unambiguous;
- binary presence as weak evidence only.

The resolver must support the common migration state where both mkinitcpio and dracut binaries remain installed but mkinitcpio hooks are masked and dracut integration is active.

### mkinitcpio

Useful evidence includes:

- explicit `kernel-install` selection;
- active mkinitcpio pacman hooks;
- presets in `/etc/mkinitcpio.d/` where applicable;
- UKI output declarations in presets;
- distro default only when no stronger competing evidence exists;
- binary presence as weak evidence only.

### Booster

Useful evidence includes:

- explicit generator configuration if present;
- Booster pacman integration;
- `/etc/booster.yaml` as configuration evidence;
- generated `booster-*.img` artifacts as supporting evidence;
- `/usr/lib/booster/regenerate_images` availability.

The rebuild command uses the documented helper rather than reimplementing kernel enumeration.

## `BootRebuildPlan`

The resolver returns an immutable plan containing at minimum:

- selected mechanism/backend name;
- primary command argv;
- optional orchestration/artifact stages;
- optional known bootloader integration stages;
- evidence used for selection;
- human-readable diagnostics.

A plan is either valid and executable or resolution raises a domain error. There is no empty-command plan.

`systemd-inhibit` is applied only when decorating a valid executable command.

## Preflight safety invariant

Graphics mode switching currently mutates services/files before `rebuild_initramfs()` discovers whether a rebuild is possible. This change moves boot resolution earlier.

For `--switch integrated`, `--switch hybrid`, `--switch nvidia` and other flows that require rebuilding boot artifacts:

1. resolve a `BootRebuildPlan` first;
2. if resolution fails, exit with no graphics/service/filesystem mutation;
3. only after successful preflight perform existing graphics configuration changes;
4. execute the already-resolved plan.

Tests must assert that resolution errors call none of:

- `systemctl` enable/disable;
- `cleanup()`;
- `create_file()`;
- real initramfs/UKI/bootloader commands.

This is a behavioral safety guarantee, not merely an implementation detail.

## Domain errors

Introduce exceptions owned by the boot subsystem:

- `BootRebuildError` — base error;
- `NoBootBackendFoundError` — no supported configured generator can be established;
- `AmbiguousBootBackendError` — competing candidates have equally authoritative evidence;
- `UnsupportedBootIntegrationError` — generator can be resolved but downstream UKI/bootloader integration cannot be updated safely;
- `BootRebuildCommandError` — a resolved rebuild command exits unsuccessfully.

Backends raise domain errors rather than calling `sys.exit()`.

The CLI catches these at its boundary, logs a clear error and returns/exits consistently with existing EnvyControl behavior.

Preflight errors must state that no system files were modified when that guarantee is true.

Verbose diagnostics should list candidates and the evidence that caused selection/rejection.

## Compatibility behavior

Existing supported non-Arch paths must retain their observable rebuild commands unless a stronger explicit orchestration configuration supersedes them:

- rpm-ostree systems;
- Debian/Ubuntu -> `update-initramfs -u -k all`;
- RHEL/SUSE -> dracut regenerate-all;
- ALT Linux -> `make-initrd`.

The refactor must add characterization tests before moving these behaviors.

## Packaging

Keep the current lightweight packaging model.

`setup.py` remains authoritative and changes from one to two runtime modules:

- `envycontrol`;
- `envycontrol_boot`.

No new runtime third-party dependency is required for this design.

A larger package migration is explicitly deferred.

## TDD strategy

Every production behavior follows RED -> GREEN -> REFACTOR.

Required regression/characterization scenarios include at minimum:

1. Arch + active mkinitcpio -> `mkinitcpio -P`.
2. Arch + active dracut -> `dracut -f --regenerate-all`; mkinitcpio is never executed.
3. Arch + active Booster -> `/usr/lib/booster/regenerate_images`.
4. Arch + dracut active + mkinitcpio binary still installed + mkinitcpio hooks masked -> dracut wins.
5. Arch + two genuinely active equally authoritative generators -> `AmbiguousBootBackendError`.
6. Ambiguous/no-backend preflight -> zero graphics/system side effects.
7. Explicit `kernel-install` generator configuration outranks weak distro/binary evidence.
8. `kernel-install` orchestration executes once and does not duplicate generator/UKI stages.
9. UKI already managed by mkinitcpio/dracut/kernel-install -> no duplicate `ukify` invocation.
10. Known Limine native integration -> supported pipeline without duplicate updates.
11. Unknown/manual Limine integration where safety cannot be proven -> preflight error.
12. rpm-ostree compatibility.
13. Debian/update-initramfs compatibility.
14. RHEL/SUSE/dracut compatibility.
15. ALT/make-initrd compatibility.
16. Unknown system -> domain error, not an empty inhibited command.
17. `systemd-inhibit` wraps only a valid command.
18. command failure -> `BootRebuildCommandError`/equivalent observable CLI failure.
19. verbose diagnostics explain why the selected backend won.

Property tests are appropriate for deterministic resolver invariants, for example: adding only weaker evidence must not displace a candidate selected by unique stronger evidence.

## Host safety and VM verification

All normal tests use fake probes, fake runners, monkeypatching and temporary paths.

No normal test may execute a real:

- graphics-mode switch;
- `systemctl` mutation;
- dracut/mkinitcpio/Booster rebuild;
- `kernel-install add-all`;
- ukify build;
- Limine update;
- write under `/etc`, `/usr`, `/lib` or machine-global boot paths.

Real end-to-end verification remains behind `scripts/verify/require-disposable-vm.sh` and the existing three-gate disposable-VM invariant. The developer workstation is never a fallback.

The VM harness should eventually include fixtures/images representing at least mkinitcpio and dracut paths; Booster/kernel-install/Limine real validation may remain `NOT EXECUTED` when the corresponding disposable VM image is unavailable, but mocked tests do not claim those real-environment cases passed.

## Mutation and quality gates

The repository currently has a measured mutation score of 59.09%, below the mandatory 60% floor. Per `CLAUDE.md`, this behavior-changing feature cannot be declared complete until a fresh run reaches at least 60%.

Requirements:

- add `envycontrol_boot.py` to mutmut scope;
- do not exclude meaningful new resolver/backend logic to inflate the score;
- strengthen assertions until the fresh overall measured score reaches >=60%;
- preserve branch coverage >=80%;
- critical pure resolver logic targets >=90% branch coverage;
- Ruff, mypy, pre-commit, Security and PR verification remain green.

## Documentation updates required with implementation

- `CLAUDE.md` and byte-identical `AGENTS.md` if the documented system boundary/backend list changes;
- `docs/CLI_CONTRACT.md` for new observable errors/diagnostics;
- `docs/COMMAND_PERMISSIONS.md` for new commands and preflight semantics;
- `docs/FACTS.md` for verified architecture/results;
- `docs/FINDINGS.md` for genuinely non-obvious discoveries;
- README only if user-facing supported boot mechanisms need clarification.

## Acceptance criteria

The feature is complete only when all of the following are true:

1. Plain Arch using dracut no longer selects mkinitcpio merely because `/etc/arch-release` exists.
2. Plain Arch using Booster selects the documented Booster regeneration helper.
3. Plain Arch using mkinitcpio retains `mkinitcpio -P` behavior.
4. Strong explicit/configured evidence wins over weak binary/distro evidence.
5. Ambiguous configurations fail before any machine-global graphics mutation.
6. Unknown systems never execute an empty `systemd-inhibit` command.
7. `kernel-install`, UKI and Limine are modeled as separate responsibilities and do not cause duplicate rebuild/update stages.
8. Existing non-Arch supported rebuild paths retain tests and behavior.
9. Unit/integration tests remain safe on a normal host and require no root/GPU/real boot tooling.
10. Destructive real verification is attempted only in a disposable EnvyControl VM; otherwise reported `NOT EXECUTED — requires disposable VM`.
11. Branch coverage remains >=80%, resolver/core logic targets >=90% where practical.
12. Fresh mutation score, including `envycontrol_boot.py`, reaches >=60%.
13. Ruff, mypy, pre-commit, Security, CI and agentic PR verification pass on the final head.
14. No runtime third-party dependency is introduced merely to implement the abstraction.
15. The public console entry point remains `envycontrol=envycontrol:main`.

## Deferred follow-up

If the original “hybrid boots but NVIDIA is not detected” problem remains reproducible after the correct boot-rebuild pipeline is selected and executed, investigate early NVIDIA module inclusion separately for the active generator:

- mkinitcpio `MODULES=()`;
- dracut `force_drivers`;
- Booster `modules_force_load`.

That work requires its own root-cause evidence and must not be silently bundled into this feature.
