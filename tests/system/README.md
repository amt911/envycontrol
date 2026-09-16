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

The fixture binaries under `tests/system/fixtures/bin/` intercept service, hardware-discovery and initramfs commands. EnvyControl is still allowed to create/remove its normal configuration paths during `system-vm.sh`; that is why this verification is VM-only even though external commands are faked.
