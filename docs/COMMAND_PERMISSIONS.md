# EnvyControl command permissions and system impact

This is the authoritative map of privilege requirements and machine-global side effects. Update it in the same change as the affected CLI operation.

| Operation | Root | Reads | Writes/removes | Services / external commands | Boot artifacts | VM-only real verification |
| --- | --- | --- | --- | --- | --- | --- |
| `--version` / `--help` | No | None beyond Python/package metadata | None | None | No | No |
| `--query` | No | Existence of blacklist, integrated udev legacy/current marker, Xorg config and modeset config | None | None | No | No |
| `--cache-query` | No | `/var/cache/envycontrol/cache.json` if present | None | None | No | No |
| `--cache-create` | Yes | Current-mode marker paths; `lspci` output | `/var/cache/envycontrol/cache.json` and parent directory | `lspci` | No | **Yes** for real cache/hardware run |
| `--cache-delete` | Yes | Cache path existence is not prechecked by the static method | Removes cache file and then parent directories | None | No | **Yes** for real path mutation |
| `--switch integrated` | Yes | Boot preflight sources; current cache/mode state after preflight; managed path existence | Removes prior managed files; writes `/etc/modprobe.d/blacklist-nvidia.conf` and `/etc/udev/rules.d/50-remove-nvidia.rules` | `systemctl disable nvidia-persistenced.service`; selected boot command; optional `systemd-inhibit` | Yes | **Yes** |
| `--switch hybrid` | Yes | Boot preflight sources; current cache/mode state after preflight; managed path existence | Removes prior managed files; writes `/etc/modprobe.d/nvidia.conf`; optional `/etc/udev/rules.d/80-nvidia-pm.rules`; cache can be refreshed only after successful preflight | `systemctl enable nvidia-persistenced.service`; selected boot command; optional `systemd-inhibit`; `lspci` if cache refresh needs it | Yes | **Yes** |
| `--switch nvidia` | Yes | Boot preflight sources; current cache/mode state; `lspci`; display-manager file; optional `/usr/bin/xrandr` and provider output; existing SDDM Xsetup | Removes prior managed files; writes `/etc/X11/xorg.conf`, `/etc/modprobe.d/nvidia.conf`, optional `/etc/X11/xorg.conf.d/10-nvidia.conf`; may back up/replace `/usr/share/sddm/scripts/Xsetup`; or write LightDM script/config | `systemctl enable nvidia-persistenced.service`; `lspci`; optional `xrandr`; `chmod`; selected boot command; optional `systemd-inhibit` | Yes | **Yes** |
| `--reset-sddm` | Yes | Current cache/mode state through legacy adapter ordering | Writes `/usr/share/sddm/scripts/Xsetup`, executable; cache may refresh before its later root assertion | `chmod`; possible `lspci` through cache refresh | No | **Yes** |
| `--reset` | Yes | Boot preflight sources; current cache/mode state after successful preflight; managed path existence; optional SDDM backup | Removes managed configuration and cache; restores SDDM backup when present | selected boot command; optional `systemd-inhibit`; possible `lspci` after successful preflight through cache handling | Yes | **Yes** |

## Boot preflight reads

Before `--switch` or `--reset` mutates anything, `envycontrol_boot.LocalSystemProbe` may inspect command availability and read/examine configuration such as:

- distro markers including `/etc/arch-release`, `/etc/debian_version`, `/etc/redhat-release`, `/usr/lib/endeavouros-release`, `/etc/altlinux-release`, OSTree paths and zypper availability;
- dracut configuration and pacman hooks under `/etc/dracut.conf*`, `/usr/share/libalpm/hooks/` and `/etc/pacman.d/hooks/`;
- mkinitcpio pacman hooks;
- `/etc/booster.yaml` and `/usr/lib/booster/regenerate_images`;
- `/etc/kernel/install.conf` and availability of `kernel-install`;
- Limine configuration (`/etc/default/limine`, `/etc/limine-entry-tool.conf`) and relevant pacman hooks.

These probes are read-only. Failure to resolve one safe plan aborts before `CachedConfig.adapter()` is entered.

## Boot command selection

The coordinator may select:

- OSTree: `rpm-ostree initramfs --enable --arg=--force`;
- Debian-family: `update-initramfs -u -k all`;
- dracut: `dracut -f --regenerate-all`;
- EndeavourOS with native helper: `dracut-rebuild`;
- ALT Linux: `make-initrd`;
- mkinitcpio: `mkinitcpio -P`;
- Booster: `/usr/lib/booster/regenerate_images`;
- authoritative kernel-install configuration: a single `kernel-install add-all` stage.

When `systemd-inhibit` is available, the selected stage is wrapped with it. Known native Limine integration does not add a duplicate command; unsupported/manual Limine arrangements fail preflight.

The resolver uses evidence strength, not only installed binaries. In particular, Arch with active dracut and mkinitcpio still installed must select dracut rather than executing mkinitcpio.

## Host-test guard

Normal pytest runs block real writes/removals in machine-global roots and block dangerous command execution. The guarded command set includes the legacy service/initramfs commands plus Booster regeneration, `kernel-install`, `ukify`, and Limine-related commands. Tests may replace those boundaries only with controlled fakes.

Real execution of any GPU switch, boot rebuild, kernel-install/UKI operation, Limine update, service mutation, or global filesystem mutation is disposable-VM-only. `scripts/verify/require-disposable-vm.sh` must positively prove explicit opt-in, the VM sentinel and virtualization. There is no host override.
