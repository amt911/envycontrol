# EnvyControl Agentic Development Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the temporary `claude-md/` material into a native, executable EnvyControl development workflow with mandatory TDD, safe host-side tests, coverage/mutation gates, Python quality tooling, VM-only destructive verification, project-specific agent documentation, and CI.

**Architecture:** Keep `envycontrol.py` and `setup.py` as the current runtime/package shape. Build development controls around that code: pytest characterisation tests with fail-closed host guards, project documentation that defines the CLI/system contract, Python-native quality tooling, separate CI/security/mutation workflows, and a disposable-VM-only system verification layer. Delete `claude-md/` only after every useful concept has an adapted destination and all cross-references pass.

**Tech Stack:** Python 3, setuptools, pytest, pytest-cov/coverage.py, Hypothesis, Ruff, mypy, mutmut, pre-commit, pip-audit, Semgrep, vulture, markdownlint, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-16-agentic-development-foundation-design.md`

## Global Constraints

- **Never run destructive verification on the developer's real host.** Any operation capable of changing GPU mode, `/etc`, `/usr`, `/var/cache/envycontrol`, udev, Xorg, display managers, systemd services, kernel-module configuration, or initramfs state is disposable-VM-only.
- A destructive VM test proceeds only when all three independent gates pass: `ENVYCONTROL_SYSTEM_TEST_VM=1`, `/etc/envycontrol-test-vm` exists, and `systemd-detect-virt --vm` positively identifies a VM. Missing or ambiguous evidence means abort before mutation.
- There is no `--force-host`, `--i-know-what-im-doing`, environment bypass, or equivalent escape hatch.
- Normal pytest runs must not require root, a real NVIDIA GPU, a real display manager, or a real initramfs tool.
- Preserve current observable EnvyControl behavior unless a change is strictly required by a demonstrated failing test.
- Preserve `setup.py` and the existing `envycontrol=envycontrol:main` console entry point.
- `pyproject.toml` is for development-tool configuration; it must not silently migrate packaging away from the current setuptools setup in this change.
- Root `CLAUDE.md` and root `AGENTS.md` must be byte-for-byte identical and enforced by a test.
- New logic and bug fixes follow mandatory Red -> Green -> Refactor.
- Coverage floor is 80% statement/branch coverage for the measured executable scope; critical pure logic targets at least 90%. The floor is not lowered to make CI green.
- Mutation testing uses a measured baseline. Once blocking, 60% is the absolute floor and the threshold only ratchets upward.
- Heavy jobs such as full coverage and mutation runs use the documented 6 GB memory cgroup and capped tool concurrency.
- Never merge a PR automatically. Default agent behavior is no push unless the explicitly documented unattended mode is active.
- Use current supported GitHub Actions majors verified during planning: `actions/checkout@v7` and `actions/setup-python@v7`; pin explicit stable Python versions rather than `3.x`.

---

## File Structure Locked by This Plan

### Runtime files preserved

- `envycontrol.py` — production implementation; only minimal testability fixes allowed, each behind a demonstrated failing test.
- `setup.py` — packaging and console-script entry point; remain functional.
- `flake.nix` — existing Nix package/dev shell; only add development tooling if verification proves it is necessary and does not change runtime packaging.

### New root/process files

- `CLAUDE.md` — canonical project-specific agent rules.
- `AGENTS.md` — exact copy of `CLAUDE.md`.
- `pyproject.toml` — pytest, coverage, Ruff, mypy, and mutmut configuration only.
- `requirements-dev.txt` — development/test tools, separate from runtime installation.
- `.pre-commit-config.yaml` — pre-commit and pre-push gates.
- `.markdownlint.jsonc` — Markdown rules adapted from the temporary template.

### New project documentation

- `docs/CLI_CONTRACT.md`
- `docs/COMMAND_PERMISSIONS.md`
- `docs/FACTS.md`
- `docs/FINDINGS.md`
- `docs/USER_STORIES.md`
- `docs/PROMPT_TEMPLATES.md`

### New automated tests

- `tests/conftest.py`
- `tests/test_agent_docs.py`
- `tests/test_host_safety.py`
- `tests/test_detection.py`
- `tests/test_configuration_generation.py`
- `tests/test_cache.py`
- `tests/test_initramfs.py`
- `tests/test_modes.py`
- `tests/test_cli.py`
- `tests/test_properties.py`
- `tests/test_vm_guard.py`

### New verification/tool scripts

- `scripts/check_mutation_score.py`
- `scripts/verify/require-disposable-vm.sh`
- `scripts/verify/smoke-cli.sh`
- `scripts/verify/system-vm.sh`
- `scripts/verify/verify-pr.sh`
- `tests/system/fixtures/bin/lspci`
- `tests/system/fixtures/bin/systemctl`
- `tests/system/fixtures/bin/mkinitcpio`
- `tests/system/fixtures/bin/systemd-inhibit`
- `tests/system/fixtures/bin/xrandr`

### GitHub automation

- `.github/dependabot.yml`
- `.github/workflows/ci.yml`
- `.github/workflows/mutation.yml`
- `.github/workflows/security.yml`

### Existing files modified

- `.gitignore` — pytest/coverage/Ruff/mypy/mutmut/venv artifacts.
- `README.md` — small development pointer only; keep it a product README.

### Temporary tree deleted last

- `claude-md/` — remove every file only after adapted replacements exist and verification passes.

---

### Task 1: Establish canonical EnvyControl agent instructions and core project docs

**Files:**
- Create: `CLAUDE.md`
- Create: `AGENTS.md`
- Create: `docs/CLI_CONTRACT.md`
- Create: `docs/COMMAND_PERMISSIONS.md`
- Create: `docs/FACTS.md`
- Create: `docs/FINDINGS.md`
- Create: `docs/USER_STORIES.md`
- Create: `.markdownlint.jsonc`
- Modify: `README.md`

**Interfaces:**
- Consumes: the approved design spec, current `envycontrol.py`, current README, and the complete temporary `claude-md/` template tree.
- Produces: the canonical rules and contracts every later task/tests/workflow must reference.

- [ ] **Step 1: Write `CLAUDE.md` for this repository, not for the template repository.**

It must contain these project-specific sections in this order so future agents can locate rules predictably:

```text
# EnvyControl — Agent Guide
Start here
Safety invariant: disposable VM only
Project architecture
CLI and system boundaries
Superpowers workflow and mode switches
Heavy jobs and memory cgroup
Tests and quality
TDD — mandatory
Coverage gate
Property-based testing
Mutation gate
Real-environment verification
Debugging discipline
Agentic PR verification
Agent orchestration
Reuse first
Working rules
Git & GitHub
```

The VM-only invariant must appear in **Start here**, **Tests and quality**, **Real-environment verification**, **Agentic PR verification**, and **Working rules**. Each occurrence must explicitly say that absence of a valid disposable VM means destructive verification is reported as `NOT EXECUTED`; the real host is never a fallback.

- [ ] **Step 2: Adapt generic/tool-specific governance without inventing unavailable capabilities.**

For `graphify` and Superpowers, use the rule: if the current agent exposes the capability, it must use it; if not, it follows the equivalent documented workflow manually and records that the tool was unavailable. Never instruct an agent to fabricate tool output. Remove pnpm/Nest/Next/Prisma/Playwright/Maestro/UI-specific rules and replace their engineering purpose with Python CLI/Linux equivalents.

- [ ] **Step 3: Make `AGENTS.md` an exact byte copy of `CLAUDE.md`.**

Run after writing both:

```bash
cmp -s CLAUDE.md AGENTS.md
```

Expected: exit status `0`.

- [ ] **Step 4: Create the CLI and system-impact contracts from current code.**

`docs/CLI_CONTRACT.md` records at minimum `--version`, `--query`, `--switch {integrated,hybrid,nvidia}`, `--dm`, `--force-comp`, `--coolbits`, `--rtd3`, `--use-nvidia-current`, `--reset-sddm`, `--reset`, `--cache-create`, `--cache-delete`, `--cache-query`, and `--verbose`, including root expectations, output/reboot semantics, and errors observable today.

`docs/COMMAND_PERMISSIONS.md` gets one row per operation with these columns:

```text
Operation | Root | Reads | Writes/removes | Services/external commands | Initramfs | VM-only real verification
```

Populate it from `envycontrol.py`; do not infer undocumented side effects.

- [ ] **Step 5: Seed FACTS, FINDINGS, and USER_STORIES with only verified current behavior.**

Every FACTS entry includes `(verified: read <file>:<symbol>, 2026-09-16)` or a later real command when executed. FINDINGS starts empty except for genuinely non-obvious facts discovered during implementation; do not copy anecdotes/timings from another project. USER_STORIES describe the existing query/switch/reset/cache journeys and acceptance criteria, not a future wishlist.

- [ ] **Step 6: Add only a concise development pointer to README.**

Add a `Development` paragraph linking `CLAUDE.md`, `docs/CLI_CONTRACT.md`, and `docs/COMMAND_PERMISSIONS.md`. Do not replace or rewrite the user-facing install/usage sections.

- [ ] **Step 7: Verify documentation consistency.**

Run:

```bash
cmp -s CLAUDE.md AGENTS.md
rg -n '<[^>]+>|TBD|TODO|@<scope>|pnpm|Playwright|Maestro|NestJS|Next\.js|Prisma' \
  CLAUDE.md AGENTS.md docs/CLI_CONTRACT.md docs/COMMAND_PERMISSIONS.md \
  docs/FACTS.md docs/FINDINGS.md docs/USER_STORIES.md
```

Expected: `cmp` succeeds; `rg` returns no template placeholders or unrelated web-stack terms.

- [ ] **Step 8: Commit.**

```bash
git add CLAUDE.md AGENTS.md README.md .markdownlint.jsonc docs/CLI_CONTRACT.md \
  docs/COMMAND_PERMISSIONS.md docs/FACTS.md docs/FINDINGS.md docs/USER_STORIES.md
git commit -m "docs: adapt agent workflow to envycontrol"
```

---

### Task 2: Add Python development configuration without changing runtime packaging

**Files:**
- Create: `pyproject.toml`
- Create: `requirements-dev.txt`
- Modify: `.gitignore`
- Test: `tests/test_agent_docs.py`

**Interfaces:**
- Consumes: Task 1 canonical docs.
- Produces: installable development toolchain and machine-enforced `CLAUDE.md == AGENTS.md` invariant.

- [ ] **Step 1: Add the first failing repository-invariant test.**

Create `tests/test_agent_docs.py` with:

```python
from pathlib import Path


def test_agents_md_is_exact_copy_of_claude_md():
    root = Path(__file__).resolve().parents[1]
    assert (root / "AGENTS.md").read_bytes() == (root / "CLAUDE.md").read_bytes()
```

Temporarily change one byte in a working-tree copy of `AGENTS.md`, run the test, observe failure, and restore the file before continuing. This proves the test can go red without committing the deliberate mismatch.

- [ ] **Step 2: Add development dependencies separately from runtime.**

`requirements-dev.txt` must include the test/quality tools used by this plan: `pytest`, `pytest-cov`, `coverage`, `hypothesis`, `ruff`, `mypy`, `mutmut`, `pre-commit`, `pip-audit`, `semgrep`, and `vulture`. Do not add any of them to `setup.py` install requirements.

- [ ] **Step 3: Add tool-only `pyproject.toml`.**

Configure:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["-ra", "--strict-config", "--strict-markers"]

[tool.coverage.run]
branch = true
source = ["envycontrol"]

[tool.coverage.report]
show_missing = true
skip_covered = false
fail_under = 80

[tool.ruff]
target-version = "py310"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "W", "I", "B", "UP", "SIM"]

[tool.mypy]
python_version = "3.10"
warn_unused_configs = true
check_untyped_defs = true
no_implicit_optional = true

[tool.mutmut]
source_paths = ["envycontrol.py"]
pytest_add_cli_args_test_selection = ["tests/"]
```

Do **not** add `[build-system]` or `[project]` in this task; that would change packaging semantics beyond the approved scope.

- [ ] **Step 4: Expand `.gitignore`.**

Add `.venv/`, `.pytest_cache/`, `.coverage`, `htmlcov/`, `.hypothesis/`, `.ruff_cache/`, `.mypy_cache/`, `mutants/`, `.mutmut-cache`, and generated mutation reports if the installed mutmut version creates them.

- [ ] **Step 5: Prove packaging still works before adding broad tests.**

Run in a clean virtual environment:

```bash
python -m pip install -e .
python -m envycontrol --version
python -c 'import envycontrol; assert envycontrol.VERSION == "3.5.2"'
```

Expected: editable install succeeds, version command prints `3.5.2`, import assertion succeeds.

- [ ] **Step 6: Run the invariant test green.**

```bash
python -m pytest tests/test_agent_docs.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit.**

```bash
git add pyproject.toml requirements-dev.txt .gitignore tests/test_agent_docs.py
git commit -m "test: bootstrap python quality tooling"
```

---

### Task 3: Build fail-closed host-safety guards before testing system behavior

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/test_host_safety.py`

**Interfaces:**
- Produces: an autouse pytest guard that blocks the real mutation/subprocess boundaries currently used by `envycontrol.py`.

- [ ] **Step 1: Write failing safety tests first.**

Tests must prove at least these cases are rejected during a normal pytest run:

```python

def test_real_etc_write_is_blocked():
    envycontrol.create_file("/etc/modprobe.d/envycontrol-test.conf", "unsafe")


def test_real_systemctl_is_blocked():
    subprocess.run(["systemctl", "disable", "nvidia-persistenced.service"])
```

Before the guard exists, run each focused test and confirm it would reach the real boundary. Do **not** allow the call to complete: initially monkeypatch the concrete primitive inside the test to raise a sentinel exception proving reachability. The RED condition is that the repository-level guard is absent, not that a real `/etc` write is attempted.

- [ ] **Step 2: Implement an autouse guard in `tests/conftest.py`.**

The guard wraps the primitives the current production code uses and raises `UnsafeHostMutation` when a normal test attempts:

```text
write/append/create below /etc, /usr, /var/cache/envycontrol
os.remove/os.removedirs/os.makedirs on those protected targets
subprocess.run for systemctl, dracut, dracut-rebuild, mkinitcpio, update-initramfs,
rpm-ostree, make-initrd, systemd-inhibit, or chmod
subprocess.check_output for lspci/xrandr unless the individual test replaces it
```

Reads may be permitted only when the test explicitly wants read-only behavior; hardware/environment discovery must still be mocked so tests are deterministic.

- [ ] **Step 3: Prove tests can still replace boundaries safely.**

Add a test that monkeypatches `envycontrol.subprocess.run` with a recording fake, calls the relevant function, and asserts the expected command was recorded without reaching the host.

- [ ] **Step 4: Run only the safety suite.**

```bash
python -m pytest tests/test_host_safety.py -v
```

Expected: PASS, with zero root requirement and zero machine-global writes.

- [ ] **Step 5: Commit.**

```bash
git add tests/conftest.py tests/test_host_safety.py
git commit -m "test: block host system mutation"
```

---

### Task 4: Characterise detection and configuration-generation behavior

**Files:**
- Create: `tests/test_detection.py`
- Create: `tests/test_configuration_generation.py`
- Create: `tests/test_properties.py`
- Modify: `envycontrol.py` only if a failing test proves a tiny seam is required.

**Interfaces:**
- Tests: `get_nvidia_gpu_pci_bus`, `get_igpu_vendor`, `get_display_manager`, `get_amd_igpu_name`, `generate_xrandr_script`, `get_current_mode`, static configuration templates.

- [ ] **Step 1: Add table-driven RED tests for NVIDIA PCI parsing.**

Cover representative addresses such as `01:00.0`, `0a:1f.3`, and domain-prefixed `0000:65:00.0`. Assert exact Xorg `PCI:<bus>:<device>:<function>` decimal output and the existing error/exit path when no NVIDIA VGA/3D controller is present.

- [ ] **Step 2: Add detection tests for Intel, AMD, missing iGPU, display-manager symlink content, AMD provider discovery, and missing xrandr.**

Every subprocess/file read is replaced with controlled input; none may consult the real host.

- [ ] **Step 3: Add mode-inference tests.**

Use monkeypatched `os.path.exists` maps to prove integrated/hybrid/NVIDIA inference from the exact current marker files.

- [ ] **Step 4: Add Hypothesis invariants that are meaningful here.**

At minimum:

```text
- generated PCI components are decimal and non-negative for valid 8-bit/5-bit/function hex components;
- generated xrandr script always contains exactly the selected provider and the NVIDIA-0 target;
- mode inference returns only one of SUPPORTED_MODES for arbitrary protected-path existence maps.
```

Do not generate arbitrary shell input that changes the intended command language; constrain strategies to valid domain values.

- [ ] **Step 5: Run focused suite.**

```bash
python -m pytest tests/test_detection.py tests/test_configuration_generation.py tests/test_properties.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit.**

```bash
git add tests/test_detection.py tests/test_configuration_generation.py tests/test_properties.py envycontrol.py
git commit -m "test: characterize hardware detection and config generation"
```

If `envycontrol.py` was unchanged, omit it from `git add`.

---

### Task 5: Characterise cache behavior and safe CLI behavior

**Files:**
- Create: `tests/test_cache.py`
- Create: `tests/test_cli.py`
- Modify: `envycontrol.py` only behind RED tests if argparse extraction is needed for reliable in-process testing.

**Interfaces:**
- Tests: `CachedConfig`, cache JSON shape, adapter rebinding, `assert_root`, read-only CLI paths, console entry point.

- [ ] **Step 1: Write cache RED tests with the cache path redirected to `tmp_path`.**

Cover create/read/show/delete, JSON shape, hybrid-only cache creation, cached PCI bus reuse, missing-cache behavior outside hybrid, and adapter restoration expectations.

- [ ] **Step 2: Write subprocess smoke tests for commands that are inherently safe.**

Use `sys.executable` and the repository script/module to test:

```bash
python envycontrol.py --help
python envycontrol.py --version
```

Assert exit code and stable identifying output. For `--query`, run in-process with path existence mocked; do not query the developer host filesystem as the source of truth.

- [ ] **Step 3: Test root gating without running as root.**

Monkeypatch `os.geteuid` to nonzero, call `assert_root`, and assert `SystemExit(1)` plus the expected logged error path.

- [ ] **Step 4: Run focused suite.**

```bash
python -m pytest tests/test_cache.py tests/test_cli.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit.**

```bash
git add tests/test_cache.py tests/test_cli.py envycontrol.py
git commit -m "test: characterize cache and cli behavior"
```

---

### Task 6: Characterise initramfs selection and GPU-mode side effects without touching the host

**Files:**
- Create: `tests/test_initramfs.py`
- Create: `tests/test_modes.py`
- Modify: `envycontrol.py` only when a demonstrated testability defect requires a minimal seam.

**Interfaces:**
- Tests: `rebuild_initramfs`, `graphics_mode_switcher`, `cleanup`, `create_file` using temporary paths/fakes.

- [ ] **Step 1: Add RED tests for every current initramfs branch.**

Mock filesystem detection and command lookup to assert exact selected commands for OSTree, Debian/Ubuntu, RHEL/SUSE, EndeavourOS+dracut, ALT Linux, Arch, and unknown systems. Cover both presence and absence of `systemd-inhibit` and both successful/nonzero subprocess return codes.

- [ ] **Step 2: Add mode-switch side-effect tests.**

For integrated, hybrid, and NVIDIA modes, replace `cleanup`, file creation, service calls, PCI/iGPU detection, and initramfs rebuild with recording fakes. Assert the exact intended sequence/arguments and generated contents for RTD3, `nvidia-current`, Coolbits, ForceCompositionPipeline, SDDM, and LightDM branches.

- [ ] **Step 3: Add cleanup tests using redirected constants under `tmp_path`.**

Create only temporary files, run cleanup, assert managed files are removed and an SDDM backup is restored. The safety fixture must make accidental use of the real constants fail.

- [ ] **Step 4: Run focused suite under the normal host guard.**

```bash
python -m pytest tests/test_initramfs.py tests/test_modes.py -v
```

Expected: PASS without sudo and without invoking a real system command.

- [ ] **Step 5: Commit.**

```bash
git add tests/test_initramfs.py tests/test_modes.py envycontrol.py
git commit -m "test: characterize mode switching boundaries"
```

---

### Task 7: Enforce coverage, lint, typing, and dead-code checks

**Files:**
- Modify: `pyproject.toml`
- Modify: test files from Tasks 3-6 as needed for genuine uncovered behavior.

**Interfaces:**
- Produces: runnable quality commands referenced by `CLAUDE.md` and later hooks/CI.

- [ ] **Step 1: Run the first real branch-coverage measurement.**

Use the memory cgroup for the full suite:

```bash
systemd-run --user --scope --quiet \
  -p MemoryHigh=5G -p MemoryMax=6G -p MemorySwapMax=0 -- \
  python -m pytest --cov=envycontrol --cov-branch --cov-report=term-missing
```

Record the actual total in `docs/FACTS.md` with date and command. Do not copy a number from this plan.

- [ ] **Step 2: Reach the 80% gate by testing behavior, not by blanket exclusions.**

Add focused tests for real missing branches. An exclusion is allowed only for genuinely non-runnable boilerplate and must use a narrow coverage exclusion with an adjacent written reason in `pyproject.toml`.

- [ ] **Step 3: Prove the 80% gate fails.**

Temporarily run with `--cov-fail-under=101` and observe nonzero exit, then restore the configured 80% threshold. This proves the gate itself is live.

- [ ] **Step 4: Run Ruff, mypy, and vulture.**

```bash
ruff check envycontrol.py tests scripts
mypy envycontrol.py
vulture envycontrol.py tests scripts --min-confidence 80
```

Ruff is blocking. Mypy is blocking only for the configured progressive rules; do not turn on strict mode and then silence the existing module wholesale. Vulture is advisory: review every finding and document real false positives rather than deleting live compatibility paths.

- [ ] **Step 5: Commit.**

```bash
git add pyproject.toml tests docs/FACTS.md
git commit -m "test: enforce coverage and static quality"
```

---

### Task 8: Measure and wire the mutation gate without inventing a score

**Files:**
- Create: `scripts/check_mutation_score.py`
- Create: `tests/test_mutation_score.py`
- Modify: `pyproject.toml`
- Modify: `docs/FACTS.md`
- Modify: `CLAUDE.md`
- Modify: `AGENTS.md`

**Interfaces:**
- Produces: reproducible mutation score parsing/checking and the real baseline/threshold used by hooks and CI.

- [ ] **Step 1: Verify the installed mutmut CLI before depending on remembered syntax.**

Run:

```bash
mutmut --version
mutmut run --help
mutmut results --help
```

Store the version and supported commands in `docs/FACTS.md`. Current planning research confirms mutmut 3.x supports `source_paths` in `[tool.mutmut]`, but execution uses the installed CLI as ground truth.

- [ ] **Step 2: Run baseline mutation testing inside the 6 GB cgroup.**

```bash
systemd-run --user --scope --quiet \
  -p MemoryHigh=5G -p MemoryMax=6G -p MemorySwapMax=0 -- \
  mutmut run
mutmut results | tee mutation-results.txt
```

Review KILLED/SURVIVED/NO_COVERAGE/TIMEOUT separately. If the output shows test-selection or import-path problems, fix the mutation configuration before treating any score as valid.

- [ ] **Step 3: Write the score checker TDD-first against the exact observed output format.**

`tests/test_mutation_score.py` must include a captured successful result sample and assert:

```text
score = killed / (killed + survived)
NO_COVERAGE is reported separately, not silently treated as killed
threshold failure exits nonzero
threshold equality passes
malformed/empty mutmut output exits nonzero rather than guessing
```

Then implement `scripts/check_mutation_score.py` to read stdin and accept one explicit integer threshold argument.

- [ ] **Step 4: Set the real policy from the measured baseline.**

If score >= 60%, set the blocking threshold to the measured score rounded down to an integer, never below 60. If score < 60%, record the real score/date and mark mutation advisory; `CLAUDE.md`/`AGENTS.md` must say the next feature cannot be considered complete until the debt reaches 60.

After changing `CLAUDE.md`, copy it byte-for-byte to `AGENTS.md` and run the sync test.

- [ ] **Step 5: Prove the checker fails.**

Pipe the captured fixture through a threshold one point above its measured score and observe nonzero exit; then run with the committed threshold and observe success when policy says blocking.

- [ ] **Step 6: Commit.**

```bash
git add scripts/check_mutation_score.py tests/test_mutation_score.py pyproject.toml \
  docs/FACTS.md CLAUDE.md AGENTS.md
git commit -m "test: add measured mutation quality gate"
```

---

### Task 9: Add pre-commit/pre-push gates without destructive host tests

**Files:**
- Create: `.pre-commit-config.yaml`
- Modify: `CLAUDE.md`
- Modify: `AGENTS.md`

**Interfaces:**
- Consumes: quality commands and measured mutation policy from Tasks 7-8.
- Produces: local gates future agents cannot casually skip.

- [ ] **Step 1: Configure fast pre-commit hooks.**

Use `pre-commit` stages explicitly. Pre-commit runs whitespace/config checks, Ruff, agent-doc sync test, and Markdown lint/config validation. No hook gets permission to run a mode switch or real system tool.

- [ ] **Step 2: Configure pre-push hooks as local commands.**

Pre-push runs, in order:

```text
1. full pytest + 80% branch coverage inside the 6 GB cgroup
2. mypy configured checks
3. mutation run inside the 6 GB cgroup, last because it is slowest, when the measured policy is blocking
```

If mutation is still advisory from Task 8, pre-push runs it and reports the score but does not misrepresent it as a blocking 60% gate.

- [ ] **Step 3: Install both hook types in a disposable/local checkout.**

```bash
pre-commit install --hook-type pre-commit --hook-type pre-push
pre-commit run --all-files
```

Do not trigger a real `git push` merely to test the hook. Exercise pre-push manually:

```bash
pre-commit run --hook-stage pre-push --all-files
```

- [ ] **Step 4: Update canonical docs and sync AGENTS.**

Document exact hook commands, `--no-verify` as an emergency bypass that transfers responsibility to the human, and the rule that hooks never run destructive VM/system verification.

- [ ] **Step 5: Commit.**

```bash
git add .pre-commit-config.yaml CLAUDE.md AGENTS.md
git commit -m "chore: enforce local quality gates"
```

---

### Task 10: Add CI, mutation, security, and Dependabot workflows

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `.github/workflows/mutation.yml`
- Create: `.github/workflows/security.yml`
- Create: `.github/dependabot.yml`

**Interfaces:**
- Produces: remote verification matching local policy without destructive system mutation.

- [ ] **Step 1: Add `ci.yml`.**

Use `actions/checkout@v7`, `actions/setup-python@v7`, `permissions: contents: read`, an explicit stable Python version, `pip install -r requirements-dev.txt`, editable install, Ruff, mypy, and pytest coverage. CI must never call `envycontrol --switch`, `--reset`, `--reset-sddm`, cache mutation as root, or any VM system test.

- [ ] **Step 2: Add `mutation.yml`.**

Trigger only for PRs targeting `main` and relevant Python/test/tooling paths. Run mutmut with the same scope/threshold policy as local hooks and upload `mutation-results.txt` as an artifact even on failure. If Task 8 measured an advisory score below 60, use job-level advisory behavior and write the baseline/date in the workflow comments; otherwise make the score checker blocking.

- [ ] **Step 3: Add `security.yml`.**

Run:

```bash
python -m pip install -r requirements-dev.txt
pip check
pip-audit -r requirements-dev.txt
semgrep scan --config p/python --config p/secrets envycontrol.py scripts tests
```

Dependency audit is blocking for high-confidence findings that affect installed tooling/runtime. Semgrep starts advisory only if initial findings require triage; once clean, remove advisory behavior in the same PR.

- [ ] **Step 4: Add Dependabot.**

Configure monthly updates for `pip` at `/` and `github-actions` at `/`, with conservative open-PR limits. Do not add ecosystems not used by this repo.

- [ ] **Step 5: Validate YAML/config locally.**

At minimum:

```bash
python - <<'PY'
from pathlib import Path
import yaml
for path in Path('.github/workflows').glob('*.yml'):
    yaml.safe_load(path.read_text())
print('workflow yaml: PASS')
PY
```

If PyYAML is not already part of the dev toolchain, validate through pre-commit's YAML hook instead of adding a runtime dependency.

- [ ] **Step 6: Commit.**

```bash
git add .github/dependabot.yml .github/workflows/ci.yml \
  .github/workflows/mutation.yml .github/workflows/security.yml
git commit -m "ci: add python quality and security workflows"
```

---

### Task 11: Implement the disposable-VM guard and prove it fails closed

**Files:**
- Create: `scripts/verify/require-disposable-vm.sh`
- Create: `tests/test_vm_guard.py`

**Interfaces:**
- Produces: one reusable gate that every destructive system-verification script must source before mutation.

- [ ] **Step 1: Write RED tests for all refusal paths before the shell guard exists.**

Use a temporary fake `PATH` and temporary sentinel path injected only for the test harness. Cover:

```text
missing ENVYCONTROL_SYSTEM_TEST_VM -> refuse
opt-in present but sentinel missing -> refuse
opt-in + sentinel but virtualization command reports bare metal -> refuse
virtualization command missing/ambiguous -> refuse
all three gates valid -> PASS without mutating anything
```

The test must never create `/etc/envycontrol-test-vm` on the developer host; emulate the sentinel path through an environment override **available only to the guard's unit-test mode**, not to `system-vm.sh`. The production `system-vm.sh` must hardcode `/etc/envycontrol-test-vm` and cannot accept the test override.

- [ ] **Step 2: Implement `require-disposable-vm.sh`.**

Its production contract is exactly:

```text
ENVYCONTROL_SYSTEM_TEST_VM must equal 1
/etc/envycontrol-test-vm must be a regular file
systemd-detect-virt --vm must exit 0 and return a non-empty value other than none
on failure: print reason to stderr and exit nonzero before caller mutation
on success: print detected virtualization and sentinel confirmation
```

Do not implement any host-force flag.

- [ ] **Step 3: Run the guard suite on the real host and verify every destructive path refuses.**

```bash
python -m pytest tests/test_vm_guard.py -v
ENVYCONTROL_SYSTEM_TEST_VM=1 scripts/verify/require-disposable-vm.sh
```

Expected on the developer host: pytest PASS; direct production guard exits nonzero unless the machine independently satisfies the real VM gates. It must not create the sentinel itself.

- [ ] **Step 4: Commit.**

```bash
git add scripts/verify/require-disposable-vm.sh tests/test_vm_guard.py
git commit -m "test: require disposable vm for system verification"
```

---

### Task 12: Add safe smoke verification and VM-only system verification

**Files:**
- Create: `scripts/verify/smoke-cli.sh`
- Create: `scripts/verify/system-vm.sh`
- Create: `tests/system/fixtures/bin/lspci`
- Create: `tests/system/fixtures/bin/systemctl`
- Create: `tests/system/fixtures/bin/mkinitcpio`
- Create: `tests/system/fixtures/bin/systemd-inhibit`
- Create: `tests/system/fixtures/bin/xrandr`

**Interfaces:**
- Consumes: Task 11 VM gate.
- Produces: deterministic safe host smoke checks and destructive filesystem/system-command verification that can execute only in a disposable VM.

- [ ] **Step 1: Implement safe smoke verification.**

`scripts/verify/smoke-cli.sh` runs without root and asserts `--help`, `--version`, import, editable/installed console entry point when present, and non-destructive test commands. It never runs switch/reset/cache mutation operations.

- [ ] **Step 2: Implement deterministic system command fixtures.**

Fixture binaries under `tests/system/fixtures/bin/` print controlled hardware/provider output or append invocations to a log path supplied by the VM script. They must not invoke the host's real `systemctl`, initramfs commands, or hardware tools.

- [ ] **Step 3: Implement `system-vm.sh` with the guard as its first executable action.**

Before any root/file mutation, source or execute `require-disposable-vm.sh`. Then prepend the fixture-bin directory to `PATH`, use the real EnvyControl CLI to exercise selected integrated/hybrid/NVIDIA configuration flows against the VM's own filesystem, and assert observable files/command logs. Prefer discarding the VM/snapshot after the run over trusting cleanup.

The script must print phase lines such as:

```text
PASS vm-guard
PASS integrated-files
PASS integrated-initramfs-command
PASS hybrid-files
PASS nvidia-files
PASS query-after-fixture-state
```

Any failed invariant exits nonzero immediately.

- [ ] **Step 4: Prove the destructive script refuses on the real host.**

Run only the refusal path:

```bash
scripts/verify/system-vm.sh
```

Expected on bare metal: nonzero exit **before** any system mutation. Inspect timestamps/checksums of EnvyControl-managed host paths before/after if needed to prove no change occurred.

- [ ] **Step 5: Document the real VM invocation, but do not fake a successful VM run.**

In `docs/FACTS.md`, record a PASS only after it has actually run inside a disposable VM satisfying all gates. If no VM is available during this implementation, record `destructive VM verification: NOT EXECUTED — no disposable test VM available`; never substitute the developer host.

- [ ] **Step 6: Commit.**

```bash
git add scripts/verify tests/system docs/FACTS.md
git commit -m "test: add vm-only system verification"
```

---

### Task 13: Adapt the full prompt library and agentic PR verifier

**Files:**
- Create: `docs/PROMPT_TEMPLATES.md`
- Create: `scripts/verify/verify-pr.sh`
- Modify: `CLAUDE.md`
- Modify: `AGENTS.md`

**Interfaces:**
- Produces: task prompts and PR verification that use EnvyControl's real workflow and VM invariant.

- [ ] **Step 1: Rewrite every useful prompt category from the temporary library.**

Include concrete EnvyControl prompts for:

```text
bootstrap/testing foundation
new CLI feature or flag
new distro/initramfs backend
GPU-mode behavior change
bug fix/systematic debugging
packaging/release change
mutation gate rollout
reuse-first audit
debugging + agent orchestration rollout
agentic PR verification
```

Each implementation prompt references `CLAUDE.md`, TDD, coverage, `docs/COMMAND_PERMISSIONS.md`, `docs/FINDINGS.md`, and the VM-only rule where system mutation is possible.

- [ ] **Step 2: Implement `verify-pr.sh` as an orchestrator, not a destructive host runner.**

It inspects the PR/diff, runs safe host checks, and reports VM-required scenarios separately. It may invoke `system-vm.sh` only when the disposable VM environment is already present and passes its guard. If unavailable, the report says `NOT EXECUTED`; it never falls back to the current workstation.

- [ ] **Step 3: Update canonical docs with exact verifier behavior and sync AGENTS.**

Run:

```bash
cp CLAUDE.md AGENTS.md
python -m pytest tests/test_agent_docs.py -v
```

- [ ] **Step 4: Commit.**

```bash
git add docs/PROMPT_TEMPLATES.md scripts/verify/verify-pr.sh CLAUDE.md AGENTS.md
git commit -m "docs: add envycontrol prompt and pr verification workflow"
```

---

### Task 14: Remove the temporary template tree and prove adaptation completeness

**Files:**
- Delete: `claude-md/` recursively
- Modify: any cross-reference that still points into `claude-md/`

**Interfaces:**
- Produces: one source of truth with no generic template tree left behind.

- [ ] **Step 1: Build a source-to-destination checklist before deletion.**

Verify all 13 temporary files are represented by the destinations defined in the design spec. The checklist must explicitly account for meta-README/starter-kit concepts that were absorbed rather than copied.

- [ ] **Step 2: Search for stale template references.**

```bash
rg -n 'claude-md/|starter-kit|PROMPT_TEMPLATES_WEB|DESIGN-SYSTEM\.template|ENDPOINT_PERMISSIONS\.template|@<scope>|pnpm|Playwright|Maestro' . \
  --glob '!docs/superpowers/specs/**' --glob '!docs/superpowers/plans/**'
```

Expected: no unintended runtime/current-doc references.

- [ ] **Step 3: Delete `claude-md/` completely.**

```bash
git rm -r claude-md
```

- [ ] **Step 4: Run docs/config consistency checks.**

```bash
cmp -s CLAUDE.md AGENTS.md
python -m pytest tests/test_agent_docs.py -v
pre-commit run --all-files
```

Expected: PASS.

- [ ] **Step 5: Commit.**

```bash
git add -A
git commit -m "chore: remove temporary claude templates"
```

---

### Task 15: Final verification, review, and PR update

**Files:**
- Modify: PR description/comment only as needed; no unreviewed production changes.

**Interfaces:**
- Produces: evidence-backed completion state for PR #1.

- [ ] **Step 1: Run the safe full local verification.**

```bash
ruff check envycontrol.py tests scripts
mypy envycontrol.py
systemd-run --user --scope --quiet \
  -p MemoryHigh=5G -p MemoryMax=6G -p MemorySwapMax=0 -- \
  python -m pytest --cov=envycontrol --cov-branch --cov-report=term-missing
scripts/verify/smoke-cli.sh
pre-commit run --all-files
pre-commit run --hook-stage pre-push --all-files
```

Do not run `scripts/verify/system-vm.sh` on the real host except to prove its **refusal path**, which must abort before mutation.

- [ ] **Step 2: Run mutation according to the measured policy.**

Inside the 6 GB cgroup, produce fresh `mutmut results`; pass it through `scripts/check_mutation_score.py` using the committed threshold. Record the actual killed/survived/no-coverage counts in the PR report.

- [ ] **Step 3: Verify packaging.**

```bash
python -m pip install -e .
envycontrol --version
python -c 'import envycontrol; print(envycontrol.VERSION)'
```

Expected: current version remains `3.5.2` unless another commit in the branch intentionally changed the product version.

- [ ] **Step 4: Verify host integrity.**

Confirm no test/verification step modified EnvyControl-managed paths on the developer host. Review `git diff --check`, `git status`, and the final branch diff.

- [ ] **Step 5: Self-review against the approved spec.**

Check every acceptance case in `docs/superpowers/specs/2026-09-16-agentic-development-foundation-design.md` and record PASS/NOT EXECUTED with evidence. `NOT EXECUTED` is acceptable only for destructive VM verification when no disposable VM was actually available; it is never converted into PASS by running on the host.

- [ ] **Step 6: Request code review using Superpowers review flow and resolve verified findings.**

Re-run focused tests for every fix; do not accept review findings without reproduction where reproduction is applicable.

- [ ] **Step 7: Update PR #1.**

Replace the design-only manual-test section with the actual safe commands/results, mutation baseline/status, CI/tooling summary, and VM result. If VM verification was unavailable, state that plainly as `NOT EXECUTED — requires disposable VM`.

- [ ] **Step 8: Mark the PR ready only when deterministic gates pass.**

Do not merge it. Leave merge/close decisions to the user.

---

## Self-Review of This Plan

### Spec coverage

- Complete `claude-md/` adaptation: Tasks 1, 13, 14.
- Canonical `CLAUDE.md` + identical `AGENTS.md`: Tasks 1, 2, 8, 9, 13, 14.
- Mandatory TDD and regression-first bug fixes: Tasks 2-8 plus canonical docs.
- Host mutation protection: Task 3.
- 80% coverage / critical logic target: Task 7.
- Hypothesis: Task 4.
- Measured mutation baseline and 60% ratchet: Task 8.
- Ruff/mypy/vulture/security/dependency quality: Tasks 7, 10.
- pre-commit/pre-push: Task 9.
- CI/mutation/security/Dependabot: Task 10.
- VM-only destructive verification with no host override: Tasks 11-12.
- Agentic PR verification: Task 13.
- CLI contract and command permissions: Task 1.
- FACTS/FINDINGS/user stories/prompts: Tasks 1 and 13.
- Packaging preservation: Tasks 2 and 15.
- Complete deletion of temporary tree: Task 14.
- Final evidence/review/PR update: Task 15.

### Placeholder scan

This plan contains no unresolved `<...>` template placeholders and no `TBD`/`TODO` implementation placeholders. Commands that depend on measured runtime facts explicitly instruct the implementer to measure and then record the observed value rather than fabricate it.

### Interface consistency

- `CLAUDE.md` is always the source copied to `AGENTS.md`; `tests/test_agent_docs.py` enforces equality throughout.
- `scripts/verify/require-disposable-vm.sh` is the only production VM gate and `system-vm.sh` consumes it before mutation.
- `scripts/check_mutation_score.py` consumes the installed mutmut output and is shared by local/CI policy.
- Safe host tests and destructive VM tests remain separate throughout; no later task weakens that boundary.
