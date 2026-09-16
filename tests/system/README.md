# Disposable VM system verification

`tests/system/` exists only to support destructive verification inside a disposable EnvyControl test VM.

## Hard safety requirements

Never create `/etc/envycontrol-test-vm` on a developer workstation merely to make the guard pass. The sentinel belongs in a disposable VM image/snapshot that is specifically intended to be destroyed or reverted after the test.

A real system run requires all of the following:

1. boot a disposable Linux VM/snapshot;
2. provision `/etc/envycontrol-test-vm` in that VM image;
3. ensure `systemd-detect-virt --vm` positively recognizes the guest;
4. run as root with `ENVYCONTROL_SYSTEM_TEST_VM=1`;
5. execute `./scripts/verify/system-vm.sh` from the checked-out branch;
6. discard/revert the VM after the run.

If any requirement is unavailable, report **NOT EXECUTED — requires disposable VM**. Never substitute the developer host.

The fixture binaries under `tests/system/fixtures/bin/` intercept service, hardware-discovery and PATH-resolved boot commands. EnvyControl is still allowed to create/remove its normal configuration paths during `system-vm.sh`; that is why this verification is VM-only even though many external commands are faked.

## Generator-specific VM matrix

Use a fresh snapshot/image for each scenario. Do not switch a developer workstation between generators just to test EnvyControl.

- **Arch + mkinitcpio:** mkinitcpio configured as the active generator. A switch should select only `mkinitcpio -P`.
- **Arch + dracut with mkinitcpio still installed:** keep both binaries installed but configure dracut as the active integration. A switch should select only `dracut -f --regenerate-all`; seeing mkinitcpio execute is a failure.
- **Arch + Booster:** configure Booster explicitly. Booster regeneration uses the absolute path `/usr/lib/booster/regenerate_images`, so the normal fixture `PATH` cannot intercept it. Test this only in a purpose-built disposable VM and discard/revert it after the run.
- **kernel-install / UKI:** configure `/etc/kernel/install.conf` so kernel-install owns the boot artifact pipeline. The expected orchestration is a single `kernel-install add-all` stage; do not count duplicated standalone dracut/mkinitcpio/ukify work as success.
- **Limine:** known native dracut/mkinitcpio integration should not add a duplicate update command. Unknown/manual Limine arrangements must fail during preflight before EnvyControl mutates GPU/system configuration.

For every scenario capture the exit status, selected command(s), relevant generated files and the VM command log. If a scenario image is unavailable, record that scenario as **NOT EXECUTED — requires disposable VM** rather than substituting a mocked host test.
