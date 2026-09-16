import builtins
import os
import shlex
import subprocess

import pytest


class UnsafeHostMutation(RuntimeError):
    """Raised when a normal test tries to reach a real machine-global boundary."""


PROTECTED_ROOTS = (
    "/etc",
    "/usr",
    "/lib",
    "/var/cache/envycontrol",
)

DANGEROUS_RUN_COMMANDS = {
    "systemctl",
    "dracut",
    "dracut-rebuild",
    "mkinitcpio",
    "update-initramfs",
    "rpm-ostree",
    "make-initrd",
    "systemd-inhibit",
    "booster",
    "regenerate_images",
    "kernel-install",
    "ukify",
    "limine",
    "limine-update",
    "limine-entry-tool",
    "limine-dracut",
    "limine-mkinitcpio",
    "chmod",
}

DANGEROUS_DISCOVERY_COMMANDS = {"lspci", "xrandr"}


def _path_is_protected(path):
    candidate = os.path.abspath(os.fspath(path))
    return any(candidate == root or candidate.startswith(root + os.sep) for root in PROTECTED_ROOTS)


def _command_name(args):
    if isinstance(args, (str, bytes)):
        text = args.decode() if isinstance(args, bytes) else args
        parts = shlex.split(text)
        return os.path.basename(parts[0]) if parts else ""
    if not args:
        return ""
    return os.path.basename(os.fspath(args[0]))


@pytest.fixture(autouse=True)
def block_real_host_mutation(monkeypatch):
    real_open = builtins.open
    real_remove = os.remove
    real_removedirs = os.removedirs
    real_makedirs = os.makedirs
    real_run = subprocess.run
    real_check_output = subprocess.check_output

    def guarded_open(file, mode="r", *args, **kwargs):
        if any(flag in mode for flag in ("w", "a", "x", "+")) and _path_is_protected(file):
            raise UnsafeHostMutation(f"blocked protected write: {file}")
        return real_open(file, mode, *args, **kwargs)

    def guarded_remove(path, *args, **kwargs):
        if _path_is_protected(path):
            raise UnsafeHostMutation(f"blocked protected remove: {path}")
        return real_remove(path, *args, **kwargs)

    def guarded_removedirs(path, *args, **kwargs):
        if _path_is_protected(path):
            raise UnsafeHostMutation(f"blocked protected removedirs: {path}")
        return real_removedirs(path, *args, **kwargs)

    def guarded_makedirs(path, *args, **kwargs):
        if _path_is_protected(path):
            raise UnsafeHostMutation(f"blocked protected makedirs: {path}")
        return real_makedirs(path, *args, **kwargs)

    def guarded_run(args, *pargs, **kwargs):
        command = _command_name(args)
        if command in DANGEROUS_RUN_COMMANDS:
            raise UnsafeHostMutation(f"blocked dangerous command: {command}")
        return real_run(args, *pargs, **kwargs)

    def guarded_check_output(args, *pargs, **kwargs):
        command = _command_name(args)
        if command in DANGEROUS_DISCOVERY_COMMANDS:
            raise UnsafeHostMutation(f"blocked host discovery command: {command}")
        return real_check_output(args, *pargs, **kwargs)

    monkeypatch.setattr(builtins, "open", guarded_open)
    monkeypatch.setattr(os, "remove", guarded_remove)
    monkeypatch.setattr(os, "removedirs", guarded_removedirs)
    monkeypatch.setattr(os, "makedirs", guarded_makedirs)
    monkeypatch.setattr(subprocess, "run", guarded_run)
    monkeypatch.setattr(subprocess, "check_output", guarded_check_output)

    # Individual tests may override a guarded boundary only with a controlled fake.
    yield
