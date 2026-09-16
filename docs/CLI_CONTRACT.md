# EnvyControl CLI contract

This document describes the user-visible command-line contract. Change it in the same PR as any intentional CLI behavior change.

## Global behavior

- Running without arguments prints help and exits with status `1`.
- `--version` prints the current `VERSION` and exits successfully.
- `--query` prints one of `integrated`, `hybrid`, `nvidia` without requiring root.
- `--verbose` enables debug output and successful boot-preflight diagnostics.
- Mode inference remains marker-file based: default `hybrid`, `integrated` from blacklist plus integrated udev marker, and `nvidia` from Xorg plus NVIDIA modeset configuration.

## Options

| Option | Root intended | Observable contract |
| --- | --- | --- |
| `-v`, `--version` | No | Print current version and exit 0. |
| `-q`, `--query` | No | Print one of `integrated`, `hybrid`, `nvidia`. |
| `-s MODE`, `--switch MODE` | Yes | MODE is one of `integrated`, `hybrid`, `nvidia`; preflight boot rebuilding before mutation, apply mode configuration, rebuild boot artifacts, request reboot. |
| `--dm DISPLAY_MANAGER` | With `--switch nvidia` | Override display-manager detection; choices: `gdm`, `gdm3`, `sddm`, `lightdm`. |
| `--force-comp` | With `--switch nvidia` | Add `ForceCompositionPipeline` to generated NVIDIA Xorg output-class config. |
| `--coolbits [VALUE]` | With `--switch nvidia` | Add Coolbits; omitted value defaults to `28`. |
| `--rtd3 [VALUE]` | With `--switch hybrid` | Configure NVIDIA runtime D3; choices `0`–`3`, omitted value defaults to `2`. |
| `--use-nvidia-current` | With a switch | Generate `nvidia-current` module configuration instead of `nvidia`. |
| `--reset-sddm` | Yes | Replace the SDDM Xsetup script with EnvyControl's default content and mark it executable. |
| `--reset` | Yes | Preflight boot rebuilding, remove EnvyControl-managed graphics configuration, delete cache and execute the preflighted boot plan. |
| `--cache-create` | Yes | Only valid while inferred mode is `hybrid`; detect the NVIDIA PCI bus and write cache JSON. |
| `--cache-delete` | Yes | Delete cache file and its parent directory hierarchy as currently implemented. |
| `--cache-query` | No | Print cache JSON when present; otherwise print `ERROR: Could not read <cache-path>`. |
| `--verbose` | No by itself | Enable debug logging and boot-preflight evidence output. |

## Boot-rebuild preflight

`--switch` and `--reset` are fail-closed. Their ordering is part of the safety contract:

1. assert root privileges;
2. perform a read-only boot-rebuild preflight and resolve one immutable `BootRebuildPlan`;
3. only after successful preflight, construct/enter `CachedConfig.adapter()` and perform system mutations;
4. reuse that exact plan for the final boot-artifact rebuild.

A failed preflight therefore occurs before EnvyControl refreshes its cache, edits `/etc` or `/usr`, changes services, or launches a boot-rebuild command.

Backend evidence is ranked from weakest to strongest:

`BINARY_PRESENT < DISTRO_DEFAULT < GENERATED_ARTIFACT < ACTIVE_INTEGRATION < EXPLICIT_CONFIG`

A unique strongest candidate wins. Equally strong authoritative candidates fail as ambiguous instead of guessing.

Supported mechanisms include:

- rpm-ostree: `rpm-ostree initramfs --enable --arg=--force`
- Debian-family initramfs-tools: `update-initramfs -u -k all`
- dracut: `dracut -f --regenerate-all`
- EndeavourOS dracut integration: `dracut-rebuild`
- ALT Linux: `make-initrd`
- mkinitcpio: `mkinitcpio -P`
- Booster: `/usr/lib/booster/regenerate_images`

On Arch-family systems, merely having `mkinitcpio` installed must not override stronger evidence that dracut or Booster is the active generator.

## kernel-install, UKI and Limine

When `/etc/kernel/install.conf` explicitly configures a supported `initrd_generator` and `kernel-install` is available, kernel-install is authoritative. The resolved plan executes one `kernel-install add-all` stage rather than duplicating generator/UKI work.

Known native Limine hooks are treated as part of the selected generator pipeline and do not cause a duplicate update stage. If Limine configuration is detected but EnvyControl cannot prove a supported native integration, preflight fails closed before mutation.

## Verbose diagnostics

With `--verbose`, a successful switch/reset preflight logs the selected backend and every diagnostic/evidence string stored in the plan. Normal output remains concise without `--verbose`.

## Errors and non-success paths

- Invalid argparse choices exit with status `2`.
- Missing NVIDIA VGA/3D controller during PCI detection logs an error, prints `Try switching to hybrid mode first!` and exits `1`.
- `--cache-create` outside hybrid mode raises `ValueError` with the hybrid-mode requirement message.
- `assert_root()` logs `This operation requires root privileges` and exits `1`.
- A boot preflight failure (`NoBootBackendFoundError`, `AmbiguousBootBackendError`, or `UnsupportedBootIntegrationError`) exits `1` and prints `No system files were modified.`. That statement is reserved for this pre-mutation path.
- A boot stage failure after GPU/system mutations exits `1` and reports `Boot artifact rebuild failed after system changes. Resolve the error before rebooting.`. It must never claim that no changes occurred.

## Cache adapter ordering

`--switch` and `--reset` assert root and complete boot preflight **before** constructing/entering `CachedConfig.adapter()`. A boot-preflight failure cannot refresh `/var/cache/envycontrol`.

`--reset-sddm` retains its legacy adapter ordering; changing that behavior requires its own characterization and design decision.

## Compatibility rule

Do not casually normalize messages, exit statuses, operation ordering, detection precedence or marker files. First add a regression/contract test, document the intended change here, and update `docs/COMMAND_PERMISSIONS.md` when side effects differ.
