# EnvyControl CLI contract

This document describes the user-visible command-line contract implemented by `envycontrol.py`. It is a compatibility reference: change it in the same PR as any intentional CLI behavior change.

## Global behavior

- Running without arguments prints help and exits with status `1`.
- `--version` prints `VERSION` (`3.5.2` on this branch) and exits successfully.
- Mutating operations print completion text and, for graphics-mode switches, tell the user to reboot for changes to take effect.
- `--verbose` raises the root logger to `DEBUG`; several subprocess calls then inherit stdout/stderr rather than being redirected.
- Mode inference is marker-file based: default `hybrid`, `integrated` when the blacklist plus integrated udev marker exists, and `nvidia` when Xorg plus NVIDIA modeset config exists.

## Options

| Option | Root intended | Observable contract |
| --- | --- | --- |
| `-v`, `--version` | No | Print current version and exit 0. |
| `-q`, `--query` | No | Print one of `integrated`, `hybrid`, `nvidia`. |
| `-s MODE`, `--switch MODE` | Yes | MODE is one of `integrated`, `hybrid`, `nvidia`; apply mode-specific configuration and request reboot. |
| `--dm DISPLAY_MANAGER` | With `--switch nvidia` | Override display-manager detection; choices: `gdm`, `gdm3`, `sddm`, `lightdm`. |
| `--force-comp` | With `--switch nvidia` | Add `ForceCompositionPipeline` to generated NVIDIA Xorg output-class config. |
| `--coolbits [VALUE]` | With `--switch nvidia` | Add Coolbits; omitted value defaults to `28`. |
| `--rtd3 [VALUE]` | With `--switch hybrid` | Configure NVIDIA runtime D3; choices `0`–`3`, omitted value defaults to `2`. |
| `--use-nvidia-current` | With a switch | Generate `nvidia-current` module configuration instead of `nvidia`. |
| `--reset-sddm` | Yes | Replace the SDDM Xsetup script with EnvyControl's default content and mark it executable. |
| `--reset` | Yes | Remove EnvyControl-managed graphics configuration, delete cache and rebuild initramfs. |
| `--cache-create` | Yes | Only valid while inferred mode is `hybrid`; detect the NVIDIA PCI bus and write cache JSON. |
| `--cache-delete` | Yes | Delete cache file and its parent directory hierarchy as currently implemented. |
| `--cache-query` | No | Print cache JSON when present; otherwise print `ERROR: Could not read <cache-path>`. |
| `--verbose` | No by itself | Enable debug logging/output behavior. |

## Graphics modes

### integrated

The switch disables `nvidia-persistenced.service`, removes prior EnvyControl configuration, writes NVIDIA module blacklist and GPU-removal udev rules, then rebuilds initramfs.

### hybrid

The switch cleans prior configuration, enables `nvidia-persistenced.service`, writes NVIDIA modeset configuration, optionally writes RTD3 configuration/udev rules, then rebuilds initramfs.

### nvidia

The switch enables `nvidia-persistenced.service`, cleans prior configuration, detects the NVIDIA PCI BusID and integrated-GPU vendor, writes Xorg/modeset configuration, optionally writes ForceCompositionPipeline/Coolbits output-class configuration, applies SDDM or LightDM integration when relevant, then rebuilds initramfs.

## Cache adapter ordering

Current code constructs and enters `CachedConfig(args).adapter()` before `assert_root()` for `--switch`, `--reset-sddm` and `--reset`. When the inferred current mode is hybrid, the adapter can recreate cache before the later root assertion. This is existing behavior, not an endorsement. Tests must characterize it before any future change.

## Errors and non-success paths

- Missing NVIDIA VGA/3D controller during PCI detection logs an error, prints `Try switching to hybrid mode first!` and exits `1`.
- `--cache-create` outside hybrid mode raises `ValueError` with the current hybrid-mode requirement message.
- `assert_root()` logs `This operation requires root privileges` and exits `1`.
- Initramfs/service subprocess failures log errors; current switch flow still reaches its final operation-completed messages unless an exception/exit interrupts it.

## Compatibility rule

Do not casually normalize messages, exit statuses, operation ordering or marker files. First add a regression/contract test, document the intended change here and update `docs/COMMAND_PERMISSIONS.md` when side effects differ.
