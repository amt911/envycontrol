# FACTS — EnvyControl

Verified working memory for agents. One fact per line; facts must include how and when they were verified. Decisions belong in specs/`AGENTS.md`; non-obvious environment gotchas belong in `docs/FINDINGS.md`.

## Architecture and packaging

- `envycontrol.py` is the single runtime Python module and declares `VERSION = '3.5.2'`. *(verified: read `envycontrol.py:VERSION`, 2026-09-16)*
- `setup.py` installs the single `envycontrol` module and exposes `envycontrol=envycontrol:main`. *(verified: read `setup.py:setup`, 2026-09-16)*
- Runtime packaging currently declares no third-party install requirements. *(verified: read `setup.py:setup`, 2026-09-16)*

## Commands and boundaries

- Supported modes are `integrated`, `hybrid`, `nvidia`; display-manager choices are `gdm`, `gdm3`, `sddm`, `lightdm`; RTD3 choices are `0..3`. *(verified: read `envycontrol.py:SUPPORTED_*`, 2026-09-16)*
- `rebuild_initramfs()` contains explicit branches for OSTree, Debian/Ubuntu, RHEL/SUSE, EndeavourOS+dracut, ALT Linux and Arch Linux. *(verified: read `envycontrol.py:rebuild_initramfs`, 2026-09-16)*
- `get_current_mode()` defaults to `hybrid` and infers integrated/NVIDIA modes from marker-file existence. *(verified: read `envycontrol.py:get_current_mode`, 2026-09-16)*
- `CachedConfig.adapter()` recreates cache when current mode is hybrid and is entered before `assert_root()` for switch/reset flows. *(verified: read `envycontrol.py:main` and `CachedConfig.adapter`, 2026-09-16)*

## Verification state

- The host-safe pytest suite currently collects **94 tests**, all passing on the verified CI run; branch coverage is **85.15%**, above the enforced 80% floor. *(verified: GitHub Actions CI output on branch `add-claude-md`, 2026-09-16)*
- Ruff and mypy pass on the measured development scope. *(verified: GitHub Actions CI output on branch `add-claude-md`, 2026-09-16)*
- The measured `mutmut 3.8.0` baseline is **59.09%**: 533 killed, 369 survived, 0 timeouts, 0 skipped, 902 total mutants. Because this is below the non-negotiable 60% floor, mutation remains advisory; the threshold has not been lowered. *(verified: successful Mutation workflow after commit `7ac670f`, 2026-09-16)*
- Per the approved plan, the next feature or behavior-changing change MUST NOT be declared complete until a fresh mutation run reaches at least **60%**. *(verified: `docs/superpowers/plans/2026-09-16-agentic-development-foundation.md` Task 8 and measured baseline, 2026-09-16)*
- Destructive VM verification has not been executed in this chat because no disposable EnvyControl test VM is connected. Status: **NOT EXECUTED — requires disposable VM**. *(verified: execution environment capability, 2026-09-16)*
