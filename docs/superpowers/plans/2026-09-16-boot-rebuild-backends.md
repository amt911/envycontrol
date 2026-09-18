# Boot Rebuild Backends Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace distro-hardcoded initramfs rebuilding with a SOLID, preflighted boot-rebuild subsystem that correctly supports Arch mkinitcpio, dracut and Booster, preserves existing distro behavior, understands kernel-install/UKI/Limine orchestration, and fails before system mutation when the boot pipeline is ambiguous or unsupported.

**Architecture:** Keep `envycontrol.py` as the CLI/runtime entrypoint and introduce one focused runtime module, `envycontrol_boot.py`. The new module contains read-only system probing, typed detection evidence, small initramfs backends, a resolver/coordinator, immutable `BootRebuildPlan`, command execution and domain errors; `envycontrol.py` resolves a plan before graphics-mode side effects and executes the validated plan afterward.

**Tech Stack:** Python 3.10+, standard library only at runtime; pytest, pytest-cov, Hypothesis, Ruff, mypy, mutmut, pre-commit, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-16-boot-rebuild-backends-design.md`

## Global Constraints

- Never run destructive verification on the developer host; real initramfs/UKI/bootloader/systemd/GPU mutation is disposable-VM-only.
- TDD is mandatory: RED -> verify failure -> GREEN -> refactor while green.
- Preserve `envycontrol=envycontrol:main` and the lightweight `setup.py` packaging model.
- No new runtime third-party dependency.
- Arch backend selection must use configured/integration evidence, not `/etc/arch-release` alone.
- Ambiguous or unsupported boot pipelines must fail before `systemctl`, `cleanup()`, `create_file()` or boot commands execute.
- `systemd-inhibit` may wrap only a valid, non-empty prepared command.
- Preserve existing rpm-ostree, Debian/Ubuntu, RHEL/SUSE and ALT rebuild behavior.
- `kernel-install` is orchestration, `ukify` is a UKI composition stage, and Limine is downstream integration; do not model them as interchangeable initramfs generators.
- Include `envycontrol_boot.py` in coverage and mutation scope.
- Coverage floor remains 80% branch coverage; do not lower it.
- Current mutation floor remains 60%; this feature is not complete until a fresh run reaches at least 60%.
- Keep `CLAUDE.md` and `AGENTS.md` byte-for-byte identical.

---

### Task 1: Boot Domain Types, Errors, and Read-Only Probe

**Files:**

- Create: `envycontrol_boot.py`
- Create: `tests/test_boot_probe.py`
- Modify: `setup.py`

**Interfaces:**

- Produces: `EvidenceKind`, `DetectionEvidence`, `DetectionResult`, `CommandResult`, `SystemProbe`, `LocalSystemProbe`, `BootRebuildError`, `NoBootBackendFoundError`, `AmbiguousBootBackendError`, `UnsupportedBootIntegrationError`, `BootRebuildCommandError`.
- Later tasks consume these exact names.

- [ ] **Step 1: Write failing tests for immutable evidence and fakeable probe boundaries**

```python
from pathlib import Path

import envycontrol_boot as boot


def test_detection_evidence_is_immutable():
    evidence = boot.DetectionEvidence(
        kind=boot.EvidenceKind.EXPLICIT_CONFIG,
        description="initrd_generator=dracut",
    )
    assert evidence.kind is boot.EvidenceKind.EXPLICIT_CONFIG
    assert evidence.description == "initrd_generator=dracut"


def test_local_probe_reads_and_detects_commands(monkeypatch, tmp_path):
    config = tmp_path / "config"
    config.write_text("value\n", encoding="utf-8")
    monkeypatch.setattr(boot.shutil, "which", lambda name: "/usr/bin/dracut" if name == "dracut" else None)
    probe = boot.LocalSystemProbe()
    assert probe.read_text(config) == "value\n"
    assert probe.command_exists("dracut") is True
    assert probe.command_exists("mkinitcpio") is False
```

- [ ] **Step 2: Run focused tests and verify RED**

Run: `python -m pytest tests/test_boot_probe.py -v`

Expected: FAIL because `envycontrol_boot` and the named types do not exist.

- [ ] **Step 3: Implement minimal domain types and probe**

Implement in `envycontrol_boot.py`:

```python
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import Protocol
import shutil


class EvidenceKind(IntEnum):
    BINARY_PRESENT = 1
    DISTRO_DEFAULT = 2
    GENERATED_ARTIFACT = 3
    ACTIVE_INTEGRATION = 4
    EXPLICIT_CONFIG = 5


@dataclass(frozen=True)
class DetectionEvidence:
    kind: EvidenceKind
    description: str


@dataclass(frozen=True)
class DetectionResult:
    backend: str
    evidence: tuple[DetectionEvidence, ...]
    eligible: bool = True

    @property
    def strongest(self) -> EvidenceKind:
        return max((item.kind for item in self.evidence), default=EvidenceKind.BINARY_PRESENT)


@dataclass(frozen=True)
class CommandResult:
    returncode: int


class SystemProbe(Protocol):
    def exists(self, path: Path | str) -> bool: ...
    def is_file(self, path: Path | str) -> bool: ...
    def is_masked(self, path: Path | str) -> bool: ...
    def command_exists(self, name: str) -> bool: ...
    def read_text(self, path: Path | str) -> str | None: ...


class LocalSystemProbe:
    def exists(self, path: Path | str) -> bool:
        return Path(path).exists()

    def is_file(self, path: Path | str) -> bool:
        return Path(path).is_file()

    def is_masked(self, path: Path | str) -> bool:
        candidate = Path(path)
        return candidate.is_symlink() and candidate.resolve() == Path("/dev/null")

    def command_exists(self, name: str) -> bool:
        return shutil.which(name) is not None

    def read_text(self, path: Path | str) -> str | None:
        try:
            return Path(path).read_text(encoding="utf-8")
        except (FileNotFoundError, OSError):
            return None


class BootRebuildError(RuntimeError):
    pass

class NoBootBackendFoundError(BootRebuildError):
    pass

class AmbiguousBootBackendError(BootRebuildError):
    pass

class UnsupportedBootIntegrationError(BootRebuildError):
    pass

class BootRebuildCommandError(BootRebuildError):
    pass
```

Update `setup.py` from `py_modules=['envycontrol']` to `py_modules=['envycontrol', 'envycontrol_boot']`.

- [ ] **Step 4: Run tests and static checks**

Run: `python -m pytest tests/test_boot_probe.py -v && ruff check envycontrol_boot.py tests/test_boot_probe.py && mypy envycontrol_boot.py`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add envycontrol_boot.py tests/test_boot_probe.py setup.py
git commit -m "feat: add boot rebuild domain boundaries"
```

---

### Task 2: Initramfs Backend Protocol and Existing Distro Characterization

**Files:**

- Modify: `envycontrol_boot.py`
- Create: `tests/test_boot_backends.py`
- Modify: `tests/test_initramfs.py`

**Interfaces:**

- Consumes: `SystemProbe`, `DetectionResult`, `DetectionEvidence`, `EvidenceKind`.
- Produces: `InitramfsBackend`, `RpmOstreeBackend`, `UpdateInitramfsBackend`, `DracutBackend`, `MakeInitrdBackend`, `MkinitcpioBackend`, `BoosterBackend`.

- [ ] **Step 1: Write failing command-contract tests**

```python
import envycontrol_boot as boot


class FakeProbe:
    def __init__(self, paths=(), commands=()):
        self.paths = set(paths)
        self.commands = set(commands)
    def exists(self, path): return str(path) in self.paths
    def is_file(self, path): return str(path) in self.paths
    def is_masked(self, path): return False
    def command_exists(self, name): return name in self.commands
    def read_text(self, path): return None


def test_backend_commands_preserve_existing_behavior():
    probe = FakeProbe()
    assert boot.RpmOstreeBackend().build_command(probe) == (
        "rpm-ostree", "initramfs", "--enable", "--arg=--force"
    )
    assert boot.UpdateInitramfsBackend().build_command(probe) == (
        "update-initramfs", "-u", "-k", "all"
    )
    assert boot.DracutBackend().build_command(probe) == (
        "dracut", "-f", "--regenerate-all"
    )
    assert boot.MakeInitrdBackend().build_command(probe) == ("make-initrd",)
    assert boot.MkinitcpioBackend().build_command(probe) == ("mkinitcpio", "-P")
    assert boot.BoosterBackend().build_command(probe) == (
        "/usr/lib/booster/regenerate_images",
    )
```

- [ ] **Step 2: Verify RED**

Run: `python -m pytest tests/test_boot_backends.py -v`

Expected: FAIL because backend classes do not exist.

- [ ] **Step 3: Implement the narrow protocol and command builders**

Add:

```python
class InitramfsBackend(Protocol):
    name: str
    def detect(self, probe: SystemProbe) -> DetectionResult: ...
    def build_command(self, probe: SystemProbe) -> tuple[str, ...]: ...
```

Implement each named backend with a constant `name`, a pure `build_command()`, and `detect()` limited to evidence collection; no subprocess execution.

- [ ] **Step 4: Keep old `rebuild_initramfs()` tests green until integration task**

Run: `python -m pytest tests/test_boot_backends.py tests/test_initramfs.py -v`

Expected: PASS; existing `envycontrol.rebuild_initramfs()` is not yet replaced.

- [ ] **Step 5: Commit**

```bash
git add envycontrol_boot.py tests/test_boot_backends.py tests/test_initramfs.py
git commit -m "feat: add initramfs backend implementations"
```

---

### Task 3: Arch Evidence Detection for mkinitcpio, dracut, and Booster

**Files:**

- Modify: `envycontrol_boot.py`
- Create: `tests/test_boot_detection.py`

**Interfaces:**

- Produces backend `detect()` behavior using exact `EvidenceKind` precedence.
- Detection remains read-only and must not execute rebuild commands.

- [ ] **Step 1: Write RED tests for Arch migration states**

Add tests covering:

```python
def test_dracut_active_and_mkinitcpio_masked_prefers_dracut_evidence():
    probe = FakeProbe(
        paths={"/etc/arch-release", "/etc/dracut.conf.d/nvidia.conf"},
        commands={"dracut", "mkinitcpio"},
        masked={"/etc/pacman.d/hooks/90-mkinitcpio-install.hook"},
    )
    result = boot.DracutBackend().detect(probe)
    assert boot.EvidenceKind.ACTIVE_INTEGRATION in {item.kind for item in result.evidence}


def test_binary_presence_is_only_weak_evidence():
    probe = FakeProbe(commands={"mkinitcpio"})
    result = boot.MkinitcpioBackend().detect(probe)
    assert result.strongest is boot.EvidenceKind.BINARY_PRESENT


def test_booster_config_is_stronger_than_binary_presence():
    probe = FakeProbe(paths={"/etc/booster.yaml"}, commands={"booster"})
    result = boot.BoosterBackend().detect(probe)
    assert result.strongest >= boot.EvidenceKind.GENERATED_ARTIFACT
```

Use a shared test-local `FakeProbe` that can represent `paths`, `commands`, `masked`, and text contents.

- [ ] **Step 2: Verify RED**

Run: `python -m pytest tests/test_boot_detection.py -v`

Expected: FAIL because detection is not yet implemented with this evidence.

- [ ] **Step 3: Implement evidence collection**

Implement helpers that inspect only explicit known paths/configurations. Required rules:

- explicit generator config -> `EXPLICIT_CONFIG`;
- active generator hook/integration -> `ACTIVE_INTEGRATION`;
- generator-specific config/artifact -> `GENERATED_ARTIFACT`;
- `/etc/arch-release` may contribute only `DISTRO_DEFAULT` to mkinitcpio when no stronger active competing evidence exists;
- binary presence -> `BINARY_PRESENT`;
- masked mkinitcpio hooks prevent them contributing active evidence.

- [ ] **Step 4: Add a property test for evidence monotonicity**

```python
@given(st.lists(st.sampled_from(list(boot.EvidenceKind)), min_size=1))
def test_strongest_evidence_is_maximum(kinds):
    result = boot.DetectionResult(
        backend="test",
        evidence=tuple(boot.DetectionEvidence(kind, kind.name) for kind in kinds),
    )
    assert result.strongest == max(kinds)
```

- [ ] **Step 5: Run focused suite**

Run: `python -m pytest tests/test_boot_detection.py tests/test_properties.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add envycontrol_boot.py tests/test_boot_detection.py tests/test_properties.py
git commit -m "feat: detect configured Arch initramfs generators"
```

---

### Task 4: Resolver and Ambiguity Handling

**Files:**

- Modify: `envycontrol_boot.py`
- Create: `tests/test_boot_resolver.py`

**Interfaces:**

- Produces: `BootBackendResolver.resolve(probe) -> InitramfsBackend`.
- Raises: `NoBootBackendFoundError`, `AmbiguousBootBackendError`.

- [ ] **Step 1: Write failing resolver tests**

```python
def test_unique_strongest_candidate_wins():
    resolver = boot.BootBackendResolver(backends=(FakeBackend("mk", 2), FakeBackend("dracut", 4)))
    assert resolver.resolve(FakeProbe()).name == "dracut"


def test_equal_authoritative_candidates_are_ambiguous():
    resolver = boot.BootBackendResolver(backends=(FakeBackend("mk", 4), FakeBackend("dracut", 4)))
    with pytest.raises(boot.AmbiguousBootBackendError, match="mk.*dracut|dracut.*mk"):
        resolver.resolve(FakeProbe())


def test_no_eligible_backend_is_error():
    resolver = boot.BootBackendResolver(backends=(FakeBackend("none", None),))
    with pytest.raises(boot.NoBootBackendFoundError):
        resolver.resolve(FakeProbe())
```

- [ ] **Step 2: Verify RED**

Run: `python -m pytest tests/test_boot_resolver.py -v`

Expected: FAIL because resolver does not exist.

- [ ] **Step 3: Implement deterministic resolver**

Resolver rules:

```python
results = [backend.detect(probe) for backend in self.backends]
eligible = [(backend, result) for backend, result in zip(self.backends, results) if result.eligible and result.evidence]
if not eligible:
    raise NoBootBackendFoundError(...)
strongest = max(result.strongest for _, result in eligible)
winners = [(backend, result) for backend, result in eligible if result.strongest == strongest]
if len(winners) != 1:
    raise AmbiguousBootBackendError(...)
return winners[0][0]
```

Diagnostics must include candidate names and strongest evidence descriptions.

- [ ] **Step 4: Add Arch integration-resolution tests**

Cover:

- dracut active + mkinitcpio binary-only -> dracut;
- Booster active -> Booster;
- truly active dracut + mkinitcpio at same precedence -> ambiguity.

- [ ] **Step 5: Run tests**

Run: `python -m pytest tests/test_boot_resolver.py tests/test_boot_detection.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add envycontrol_boot.py tests/test_boot_resolver.py
git commit -m "feat: resolve boot backend from configuration evidence"
```

---

### Task 5: Preserve Non-Arch Distribution Behavior

**Files:**

- Modify: `envycontrol_boot.py`
- Modify: `tests/test_boot_resolver.py`
- Modify: `tests/test_initramfs.py`

**Interfaces:**

- Resolver default registry must preserve rpm-ostree, Debian/Ubuntu, RHEL/SUSE, ALT behavior.

- [ ] **Step 1: Add RED characterization tests through the new resolver**

Test exact mappings:

```text
/ostree or /sysroot/ostree -> rpm-ostree initramfs --enable --arg=--force
/etc/debian_version -> update-initramfs -u -k all
/etc/redhat-release or /usr/bin/zypper -> dracut -f --regenerate-all
/etc/altlinux-release -> make-initrd
```

Also characterize EndeavourOS + `dracut-rebuild` when its native integration is present so compatibility is not silently lost.

- [ ] **Step 2: Verify RED**

Run: `python -m pytest tests/test_boot_resolver.py -k "ostree or debian or redhat or suse or alt or endeavour" -v`

Expected: at least one FAIL until fallback evidence is wired.

- [ ] **Step 3: Implement distro-specific evidence without overriding explicit config**

Special-system evidence must be strong enough for legacy compatibility but explicit `kernel-install` generator configuration introduced later must be allowed to supersede ordinary distro defaults where the spec permits it.

- [ ] **Step 4: Run old and new characterization suites together**

Run: `python -m pytest tests/test_boot_resolver.py tests/test_initramfs.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add envycontrol_boot.py tests/test_boot_resolver.py tests/test_initramfs.py
git commit -m "feat: preserve distro boot rebuild compatibility"
```

---

### Task 6: kernel-install and UKI Orchestration

**Files:**

- Modify: `envycontrol_boot.py`
- Create: `tests/test_kernel_install.py`

**Interfaces:**

- Produces: `KernelInstallConfig`, `KernelInstallStrategy`, `BootArtifactStrategy` protocol if needed by composition.
- `KernelInstallStrategy.detect(probe)` parses `/etc/kernel/install.conf` defensively.
- Explicit `initrd_generator=` outranks weak backend evidence.

- [ ] **Step 1: Write RED parser tests**

```python
def test_kernel_install_config_parses_explicit_generators():
    probe = FakeProbe(text={
        "/etc/kernel/install.conf": "layout=uki\ninitrd_generator=dracut\nuki_generator=ukify\n"
    })
    config = boot.KernelInstallStrategy().read_config(probe)
    assert config.layout == "uki"
    assert config.initrd_generator == "dracut"
    assert config.uki_generator == "ukify"
```

Add tests for comments, whitespace, missing file, and unknown keys being ignored.

- [ ] **Step 2: Verify RED**

Run: `python -m pytest tests/test_kernel_install.py -v`

Expected: FAIL because strategy/config do not exist.

- [ ] **Step 3: Implement config parsing and orchestration decision**

`KernelInstallConfig` is frozen and contains `layout`, `initrd_generator`, `uki_generator` as `str | None`.

When config proves kernel-install owns orchestration, produce a stage whose argv is exactly:

```python
("kernel-install", "add-all")
```

Do not separately append dracut/mkinitcpio/ukify in that plan.

- [ ] **Step 4: Add RED/GREEN tests preventing duplicate UKI work**

Required assertions:

- `layout=uki`, `initrd_generator=dracut`, `uki_generator=ukify` -> one `kernel-install add-all` stage;
- mkinitcpio preset already declaring UKI output -> no standalone `ukify` stage;
- dracut native UKI config -> no standalone `ukify` stage.

- [ ] **Step 5: Run tests**

Run: `python -m pytest tests/test_kernel_install.py tests/test_boot_resolver.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add envycontrol_boot.py tests/test_kernel_install.py
git commit -m "feat: support kernel-install and UKI orchestration"
```

---

### Task 7: Limine Integration Resolution

**Files:**

- Modify: `envycontrol_boot.py`
- Create: `tests/test_limine_integration.py`

**Interfaces:**

- Produces: `BootloaderIntegration` protocol and `LimineIntegration`.
- Raises `UnsupportedBootIntegrationError` for detected Limine setups whose update path cannot be proven safe.

- [ ] **Step 1: Write RED tests for known and unknown Limine paths**

Test cases:

```python
def test_limine_presence_alone_does_not_schedule_command(): ...
def test_known_dracut_limine_native_hook_does_not_duplicate_update(): ...
def test_known_mkinitcpio_limine_hook_does_not_duplicate_update(): ...
def test_unknown_manual_limine_configuration_fails_preflight():
    with pytest.raises(boot.UnsupportedBootIntegrationError): ...
```

The tests must represent known integration using explicit hook/package-path evidence, not just a `limine` binary.

- [ ] **Step 2: Verify RED**

Run: `python -m pytest tests/test_limine_integration.py -v`

Expected: FAIL because integration resolver does not exist.

- [ ] **Step 3: Implement conservative Limine resolution**

Rules:

- no Limine evidence -> no integration stage;
- known native generator integration -> mark as already handled, add no duplicate command;
- unknown/custom Limine configuration where stale entries may result -> raise `UnsupportedBootIntegrationError` before plan creation;
- never infer support from binary presence alone.

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_limine_integration.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add envycontrol_boot.py tests/test_limine_integration.py
git commit -m "feat: resolve Limine boot integration safely"
```

---

### Task 8: Immutable BootRebuildPlan and Safe Command Execution

**Files:**

- Modify: `envycontrol_boot.py`
- Create: `tests/test_boot_plan.py`

**Interfaces:**

- Produces: `CommandRunner`, `SubprocessCommandRunner`, `BootStage`, `BootRebuildPlan`, `BootRebuildCoordinator`.
- `BootRebuildCoordinator.resolve(probe) -> BootRebuildPlan`.
- `BootRebuildPlan.execute(runner, verbose=False)` raises `BootRebuildCommandError` on non-zero stage result.

- [ ] **Step 1: Write RED tests for immutable valid plans**

```python
def test_plan_never_contains_empty_command():
    with pytest.raises(ValueError):
        boot.BootStage(name="invalid", argv=())


def test_inhibit_wraps_only_valid_command():
    runner = RecordingRunner()
    plan = boot.BootRebuildPlan(
        backend="dracut",
        stages=(boot.BootStage("initramfs", ("dracut", "-f", "--regenerate-all")),),
        evidence=(),
    )
    plan.execute(runner, inhibit=True)
    assert runner.calls == [[
        "systemd-inhibit", "--who=envycontrol", "--why", "Rebuilding boot artifacts", "--",
        "dracut", "-f", "--regenerate-all",
    ]]
```

- [ ] **Step 2: Verify RED**

Run: `python -m pytest tests/test_boot_plan.py -v`

Expected: FAIL because plan/stage/runner do not exist.

- [ ] **Step 3: Implement immutable plan and execution**

`BootStage` and `BootRebuildPlan` must be frozen dataclasses. Reject empty argv in `BootStage.__post_init__`. Inhibition is applied only during execution of an existing stage.

`SubprocessCommandRunner` preserves current behavior: verbose mode inherits stdout/stderr; quiet mode sends both to `subprocess.DEVNULL`.

- [ ] **Step 4: Add failure test**

```python
def test_nonzero_stage_raises_domain_error():
    runner = RecordingRunner(returncode=1)
    with pytest.raises(boot.BootRebuildCommandError, match="dracut"):
        plan.execute(runner)
```

- [ ] **Step 5: Run tests**

Run: `python -m pytest tests/test_boot_plan.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add envycontrol_boot.py tests/test_boot_plan.py
git commit -m "feat: add validated boot rebuild plans"
```

---

### Task 9: Preflight Integration into Graphics Mode Switching

**Files:**

- Modify: `envycontrol.py`
- Modify: `tests/test_modes.py`
- Modify: `tests/test_initramfs.py`
- Create: `tests/test_boot_preflight.py`

**Interfaces:**

- `graphics_mode_switcher(...)` resolves a `BootRebuildPlan` before any mode mutation for all switch modes.
- Existing `rebuild_initramfs()` becomes a compatibility wrapper around the new coordinator or is removed only after all call sites/tests move.

- [ ] **Step 1: Write RED safety regression**

```python
def test_preflight_failure_has_zero_system_side_effects(monkeypatch):
    effects = []
    monkeypatch.setattr(envycontrol, "cleanup", lambda: effects.append("cleanup"))
    monkeypatch.setattr(envycontrol, "create_file", lambda *args, **kwargs: effects.append("file"))
    monkeypatch.setattr(envycontrol.subprocess, "run", lambda *args, **kwargs: effects.append("subprocess"))
    monkeypatch.setattr(
        envycontrol,
        "resolve_boot_rebuild_plan",
        lambda: (_ for _ in ()).throw(envycontrol_boot.AmbiguousBootBackendError("ambiguous")),
    )
    with pytest.raises(envycontrol_boot.AmbiguousBootBackendError):
        envycontrol.graphics_mode_switcher("hybrid", None, False, None, None, False)
    assert effects == []
```

Adapt helper signature to the final integration function chosen in GREEN, but preserve the observable assertion: resolver failure occurs before any mutation.

- [ ] **Step 2: Verify RED**

Run: `python -m pytest tests/test_boot_preflight.py -v`

Expected: FAIL because preflight resolution is not yet invoked first.

- [ ] **Step 3: Integrate coordinator before side effects**

At the start of switch processing, create the probe/coordinator and resolve exactly one plan. Pass that plan through the existing mode path and execute it where `rebuild_initramfs()` used to run.

Do not resolve separately per mode branch.

- [ ] **Step 4: Add exact Arch+dracut hybrid regression**

Test that a fake Arch environment with active dracut and merely-installed mkinitcpio causes the hybrid path to execute only:

```text
dracut -f --regenerate-all
```

and never `mkinitcpio`.

- [ ] **Step 5: Preserve all three mode tests**

Run: `python -m pytest tests/test_modes.py tests/test_initramfs.py tests/test_boot_preflight.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add envycontrol.py tests/test_modes.py tests/test_initramfs.py tests/test_boot_preflight.py
git commit -m "fix: preflight boot rebuild before GPU mode changes"
```

---

### Task 10: CLI Error Boundary and Verbose Diagnostics

**Files:**

- Modify: `envycontrol.py`
- Modify: `tests/test_cli.py`
- Modify: `docs/CLI_CONTRACT.md`
- Modify: `docs/COMMAND_PERMISSIONS.md`

**Interfaces:**

- CLI catches `BootRebuildError` at one boundary.
- Preflight failures print/log actionable diagnostics and exit non-zero without claiming operation completion.

- [ ] **Step 1: Write RED CLI tests**

Required assertions:

```text
ambiguous config -> non-zero exit
message lists competing backends
message contains "No system files were modified."
no "Operation completed successfully"
--verbose includes evidence descriptions
```

- [ ] **Step 2: Verify RED**

Run: `python -m pytest tests/test_cli.py -k "boot or ambiguous or preflight" -v`

Expected: FAIL before CLI boundary exists.

- [ ] **Step 3: Implement one CLI error boundary**

Catch `BootRebuildError` around switch execution, log the domain message, print the no-mutation guarantee only for preflight failures occurring before mode mutation, and return/exit consistently with existing CLI behavior.

- [ ] **Step 4: Update observable contracts**

Document backend selection, preflight failure, new touched/read paths and commands in `docs/CLI_CONTRACT.md` and `docs/COMMAND_PERMISSIONS.md`.

- [ ] **Step 5: Run tests/docs lint**

Run: `python -m pytest tests/test_cli.py tests/test_boot_preflight.py -v && pre-commit run markdownlint --all-files`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add envycontrol.py tests/test_cli.py docs/CLI_CONTRACT.md docs/COMMAND_PERMISSIONS.md
git commit -m "feat: report boot preflight failures safely"
```

---

### Task 11: Host-Safety Guards and Disposable-VM Harness Coverage

**Files:**

- Modify: `tests/conftest.py`
- Modify: `tests/test_host_safety.py`
- Modify: `scripts/verify/system-vm.sh`
- Modify: `tests/system/README.md`
- Add fixtures under: `tests/system/fixtures/bin/` only when a newly supported command needs a fake executable.

**Interfaces:**

- Normal pytest must block real `kernel-install`, `ukify`, Booster regeneration and Limine mutation commands in addition to existing dangerous commands.
- VM script remains gated by `ENVYCONTROL_SYSTEM_TEST_VM=1`, `/etc/envycontrol-test-vm`, and positive `systemd-detect-virt --vm`.

- [ ] **Step 1: Add RED guard tests for new dangerous commands**

Parameterize at least:

```text
kernel-install add-all
/usr/lib/booster/regenerate_images
ukify build ...
limine-update / generator-specific mutation command when supported
```

Each real subprocess attempt in normal pytest must raise the host-safety exception.

- [ ] **Step 2: Verify RED**

Run: `python -m pytest tests/test_host_safety.py -v`

Expected: FAIL for newly unguarded commands.

- [ ] **Step 3: Extend the guard and VM fake command set**

Update the dangerous-command allow/deny boundary without weakening existing checks. VM fixtures may log invocations but must never be used as proof of a real host rebuild.

- [ ] **Step 4: Update VM documentation**

Describe which scenarios can be validated in a prepared disposable image and keep unavailable real environments explicitly `NOT EXECUTED`.

- [ ] **Step 5: Run safety tests**

Run: `python -m pytest tests/test_host_safety.py tests/test_vm_guard.py tests/test_verify_scripts.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add tests/conftest.py tests/test_host_safety.py scripts/verify/system-vm.sh tests/system
git commit -m "test: guard new boot rebuild commands"
```

---

### Task 12: Mutation Ratchet, Documentation, Full Verification, and PR

**Files:**

- Modify: `pyproject.toml`
- Modify: `scripts/run-mutation.sh` only if required to include the new module correctly
- Modify: `CLAUDE.md`
- Modify: `AGENTS.md`
- Modify: `docs/FACTS.md`
- Modify: `docs/FINDINGS.md`
- Modify: `README.md` only if user-facing supported boot mechanisms need a concise note

**Interfaces:**

- Mutation scope includes both `envycontrol.py` and `envycontrol_boot.py`.
- Final score must be >=60% before completion.

- [ ] **Step 1: Expand mutation and coverage scope**

Configure source paths to include both runtime modules. Do not exclude new resolver/backends merely to raise the score.

- [ ] **Step 2: Run deterministic quality suite**

Run under the repository memory policy where applicable:

```bash
python -m pytest -v
python -m pytest --cov=envycontrol --cov=envycontrol_boot --cov-branch --cov-report=term-missing
ruff check envycontrol.py envycontrol_boot.py tests scripts
mypy envycontrol.py envycontrol_boot.py
pre-commit run --all-files
./scripts/verify/verify-pr.sh
```

Expected: all PASS; branch coverage >=80%.

- [ ] **Step 3: Run fresh mutation testing**

Run: `./scripts/run-mutation.sh --advisory`

Expected: completed run over both runtime modules. Record killed/survived/timeout/total and score.

If score <60%, inspect surviving mutants in resolver/backend/preflight logic, add focused RED tests that assert externally meaningful behavior, and rerun until score >=60%. Do not lower the threshold or reclassify survivors/timeouts.

- [ ] **Step 4: Make mutation blocking once >=60%**

Update the recorded threshold/ratchet to the verified score rounded down as specified by repository policy, never below 60%.

- [ ] **Step 5: Update canonical documentation**

Record verified facts and non-obvious findings in `docs/FACTS.md` / `docs/FINDINGS.md`. Update the mutation baseline in both `CLAUDE.md` and byte-identical `AGENTS.md` in the same commit. Document that destructive real rebuild validation remains VM-only and report any unavailable VM scenarios as `NOT EXECUTED`.

- [ ] **Step 6: Run final verification on the exact final head**

Re-run the deterministic suite after all documentation/config changes. Confirm `CLAUDE.md` and `AGENTS.md` have identical bytes and no temporary workflows/scripts remain.

- [ ] **Step 7: Review diff against `main`**

Confirm production changes are limited to the approved boot-rebuild architecture/integration and necessary packaging changes. Verify no unrelated refactor entered the PR.

- [ ] **Step 8: Open a draft PR**

PR title:

```text
feat: support configurable boot rebuild backends
```

PR body must include:

- root cause: Arch was hardwired to mkinitcpio;
- supported mechanisms and SOLID architecture summary;
- preflight-before-mutation safety guarantee;
- exact CI/coverage/mutation results;
- explicit disposable-VM status for real destructive validation;
- `How to test manually` with only safe host-side commands plus separate VM-only instructions.

Do not merge the PR.

- [ ] **Step 9: Commit final docs/config**

```bash
git add pyproject.toml scripts/run-mutation.sh CLAUDE.md AGENTS.md docs README.md
git commit -m "docs: record boot backend verification"
```
