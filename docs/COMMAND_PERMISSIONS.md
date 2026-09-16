# EnvyControl command permissions and system impact

This is the authoritative map of privilege requirements and machine-global side effects. Update it in the same change as the affected CLI operation.

| Operation | Root | Reads | Writes/removes | Services / external commands | Initramfs | VM-only real verification |
| --- | --- | --- | --- | --- | --- | --- |
| `--version` / `--help` | No | None beyond Python/package metadata | None | None | No | No |
| `--query` | No | Existence of blacklist, integrated udev legacy/current marker, Xorg config and modeset config | None | None | No | No |
| `--cache-query` | No | `/var/cache/envycontrol/cache.json` if present | None | None | No | No |
| `--cache-create` | Yes | Current-mode marker paths; `lspci` output | `/var/cache/envycontrol/cache.json` and parent directory | `lspci` | No | **Yes** for real cache/hardware run |
| `--cache-delete` | Yes | Cache path existence is not prechecked by the static method | Removes cache file and then parent directories | None | No | **Yes** for real path mutation |
| `--switch integrated` | Yes | Current cache/mode state through adapter; managed path existence | Removes prior managed files; writes `/etc/modprobe.d/blacklist-nvidia.conf` and `/etc/udev/rules.d/50-remove-nvidia.rules`; cache may be refreshed before root assertion when current mode is hybrid | `systemctl disable nvidia-persistenced.service`; distro initramfs command; optional `systemd-inhibit` | Yes | **Yes** |
| `--switch hybrid` | Yes | Current cache/mode state; managed path existence | Removes prior managed files; writes `/etc/modprobe.d/nvidia.conf`; optional `/etc/udev/rules.d/80-nvidia-pm.rules`; cache may be refreshed before root assertion when current mode is hybrid | `systemctl enable nvidia-persistenced.service`; distro initramfs command; optional `systemd-inhibit`; `lspci` when cache is created | Yes | **Yes** |
| `--switch nvidia` | Yes | Current cache/mode state; `lspci`; display manager file; optional `/usr/bin/xrandr` and provider output; existing SDDM Xsetup | Removes prior managed files; writes `/etc/X11/xorg.conf`, `/etc/modprobe.d/nvidia.conf`, optional `/etc/X11/xorg.conf.d/10-nvidia.conf`; may back up/replace `/usr/share/sddm/scripts/Xsetup`; or write LightDM script/config; cache may refresh before root assertion | `systemctl enable nvidia-persistenced.service`; `lspci`; optional `xrandr`; `chmod`; distro initramfs command; optional `systemd-inhibit` | Yes | **Yes** |
| `--reset-sddm` | Yes | Current cache/mode state through adapter | Writes `/usr/share/sddm/scripts/Xsetup`, executable; cache may refresh before root assertion | `chmod`; possible `lspci` through cache refresh | No | **Yes** |
| `--reset` | Yes | Current cache/mode state; managed path existence; optional SDDM backup | Removes managed configuration and cache; restores SDDM backup when present; cache may refresh before root assertion | distro initramfs command; optional `systemd-inhibit`; possible `lspci` through cache refresh | Yes | **Yes** |

## Initramfs command selection

Current implementation selects:

- OSTree: `rpm-ostree initramfs --enable --arg=--force`;
- Debian/Ubuntu: `update-initramfs -u -k all`;
- RHEL/SUSE: `dracut --force --regenerate-all`;
- EndeavourOS with dracut: `dracut-rebuild`;
- ALT Linux: `make-initrd`;
- Arch Linux: `mkinitcpio -P`;
- unknown systems: no base initramfs command.

When `systemd-inhibit` is available, the selected command is wrapped with it. Real execution of any of these paths is disposable-VM-only.

## Safety policy

Normal pytest runs replace the above filesystem/subprocess boundaries. Destructive verification may run only after `scripts/verify/require-disposable-vm.sh` positively proves the dedicated disposable VM. No host override is permitted.
