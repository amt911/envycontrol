# FACTS — EnvyControl

Verified working memory for agents. One fact per line; facts must include how and when they were verified. Decisions belong in specs/`CLAUDE.md`; non-obvious environment gotchas belong in `docs/FINDINGS.md`.

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

- Destructive VM verification has not been executed in this chat because no disposable EnvyControl test VM is connected. Status: **NOT EXECUTED — requires disposable VM**. *(verified: execution environment capability, 2026-09-16)*
