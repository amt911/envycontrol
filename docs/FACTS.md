# FACTS — EnvyControl

Verified working memory for agents. One fact per line; facts must include how and when they were verified. Decisions belong in specs/`AGENTS.md`; non-obvious environment gotchas belong in `docs/FINDINGS.md`.

## Architecture and packaging

- `envycontrol.py` declares `VERSION = '3.6.0'` and owns the CLI, graphics-mode operations, cache behavior and integration with boot preflight/execution. `flake.nix` repeats the same version and `tests/test_release_workflow.py` keeps the two in step. *(verified: source + `pytest tests/test_release_workflow.py`, 2026-09-18)*
- `envycontrol_boot.py` owns the boot-rebuild domain model, evidence-ranked backend detection, resolver/coordinator, kernel-install/UKI/Limine handling and subprocess command runner. *(verified: source and boot-domain tests, 2026-09-16)*
- `setup.py` packages both `envycontrol` and `envycontrol_boot` and exposes `envycontrol=envycontrol:main`. Runtime packaging declares no third-party install requirements. *(verified: `setup.py` plus editable-install CI smoke, 2026-09-16)*

## Boot rebuild behavior

- Backend evidence strength is ordered `BINARY_PRESENT < DISTRO_DEFAULT < GENERATED_ARTIFACT < ACTIVE_INTEGRATION < EXPLICIT_CONFIG`; a unique strongest candidate wins and equally strong authoritative candidates fail closed as ambiguous. *(verified: `envycontrol_boot.py` and resolver/property tests, 2026-09-16)*
- Supported generator/platform commands include rpm-ostree, `update-initramfs`, dracut, EndeavourOS `dracut-rebuild`, ALT `make-initrd`, mkinitcpio and Booster `/usr/lib/booster/regenerate_images`. *(verified: backend contract tests, 2026-09-16)*
- On Arch, active dracut evidence beats mkinitcpio being merely installed; the regression test for `--switch hybrid` proves the preflighted dracut plan executes and mkinitcpio does not. *(verified: `tests/test_boot_preflight.py` and CI, 2026-09-16)*
- Explicit supported `/etc/kernel/install.conf` plus available `kernel-install` resolves to one `kernel-install add-all` stage rather than duplicated generator/ukify work. *(verified: `tests/test_kernel_install.py`, 2026-09-16)*
- Known native Limine integration adds no duplicate update stage; detected unsupported/manual Limine configuration fails preflight. *(verified: `tests/test_limine_integration.py`, 2026-09-16)*

## CLI safety ordering

- For `--switch` and `--reset`, `main()` asserts root and resolves one immutable boot plan **before** constructing/entering `CachedConfig.adapter()`; the exact same plan is reused after mutation. *(verified: `envycontrol.py`, `tests/test_cli.py`, `tests/test_boot_preflight.py`, 2026-09-16)*
- A boot preflight failure exits 1 before cache/system mutation and prints `No system files were modified.`; a boot command failure after mutation exits 1 with the distinct warning that boot-artifact rebuilding failed after system changes. *(verified: CLI/preflight tests, 2026-09-16)*
- `--verbose` logs the selected boot backend and its evidence diagnostics after successful preflight. *(verified: `tests/test_boot_verbose.py` and CI, 2026-09-16)*

## Host and VM safety

- Normal pytest blocks real global writes/removals and dangerous system commands, including Booster regeneration, `kernel-install`, `ukify` and Limine-related commands; absolute-path command attempts are covered by tests. *(verified: `tests/conftest.py`, `tests/test_host_safety.py`, CI, 2026-09-16)*
- Destructive verification requires all three independent gates: `ENVYCONTROL_SYSTEM_TEST_VM=1`, regular-file sentinel `/etc/envycontrol-test-vm`, and positive `systemd-detect-virt --vm`; there is no host override. *(verified: guard scripts and VM-guard tests, 2026-09-16)*
- Booster real verification cannot be intercepted through fixture `PATH` because its command is the absolute path `/usr/lib/booster/regenerate_images`; it requires a purpose-built disposable VM. *(verified: backend command + VM harness review, 2026-09-16)*
- Destructive VM verification has not been executed in this chat because no disposable EnvyControl test VM is connected. Status: **NOT EXECUTED — requires disposable VM**. *(verified: execution environment, 2026-09-16)*

## Verification state

- The host-safe suite collects **142 tests**, all passing on the verified CI run. *(verified: GitHub Actions CI run 35131714977, 2026-09-16)*
- Combined branch coverage across `envycontrol.py` and `envycontrol_boot.py` is **88.84%**: `envycontrol.py` 85%, `envycontrol_boot.py` 94%, above the enforced 80% floor. *(verified: GitHub Actions CI run 35131714977, 2026-09-16)*
- Ruff passes on `envycontrol.py`, `envycontrol_boot.py`, tests and scripts; mypy reports no issues in both runtime modules; pre-commit and the safe PR verifier pass. *(verified: GitHub Actions CI run 35131714977, 2026-09-16)*
- The fresh `mutmut 3.8.0` two-module baseline is **62.67%**: 878 killed, 523 survived, 1 no-tests, 0 timeouts, 0 skipped, 1402 total. The mandatory floor remains 60% and mutation is now blocking. *(verified: Mutation run 35130658652 artifact `mutmut-report`, 2026-09-16)*
