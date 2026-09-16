import logging
from types import SimpleNamespace

import pytest

import envycontrol


@pytest.mark.parametrize(
    ("present", "expected"),
    [
        ({"/ostree"}, ["rpm-ostree", "initramfs", "--enable", "--arg=--force"]),
        ({"/etc/debian_version"}, ["update-initramfs", "-u", "-k", "all"]),
        ({"/etc/redhat-release"}, ["dracut", "--force", "--regenerate-all"]),
        ({"/usr/bin/zypper"}, ["dracut", "--force", "--regenerate-all"]),
        (
            {"/usr/lib/endeavouros-release", "/usr/bin/dracut"},
            ["dracut-rebuild"],
        ),
        ({"/etc/altlinux-release"}, ["make-initrd"]),
        ({"/etc/arch-release"}, ["mkinitcpio", "-P"]),
    ],
)
def test_rebuild_initramfs_selects_distribution_command(monkeypatch, present, expected):
    calls = []
    monkeypatch.setattr(envycontrol.os.path, "exists", lambda path: path in present)
    monkeypatch.setattr(envycontrol.shutil, "which", lambda command: None)
    monkeypatch.setattr(
        envycontrol.subprocess,
        "run",
        lambda args, **kwargs: calls.append(list(args)) or SimpleNamespace(returncode=0),
    )

    envycontrol.rebuild_initramfs()

    assert calls == [expected]


def test_rebuild_initramfs_wraps_selected_command_with_systemd_inhibit(monkeypatch):
    calls = []
    monkeypatch.setattr(
        envycontrol.os.path,
        "exists",
        lambda path: path == "/etc/arch-release",
    )
    monkeypatch.setattr(envycontrol.shutil, "which", lambda command: "/usr/bin/systemd-inhibit")
    monkeypatch.setattr(
        envycontrol.subprocess,
        "run",
        lambda args, **kwargs: calls.append(list(args)) or SimpleNamespace(returncode=0),
    )

    envycontrol.rebuild_initramfs()

    assert calls == [[
        "systemd-inhibit",
        "--who=envycontrol",
        "--why",
        "Rebuilding initramfs",
        "--",
        "mkinitcpio",
        "-P",
    ]]


def test_unknown_distribution_without_inhibit_runs_no_command(monkeypatch):
    calls = []
    monkeypatch.setattr(envycontrol.os.path, "exists", lambda path: False)
    monkeypatch.setattr(envycontrol.shutil, "which", lambda command: None)
    monkeypatch.setattr(
        envycontrol.subprocess,
        "run",
        lambda args, **kwargs: calls.append(list(args)) or SimpleNamespace(returncode=0),
    )
    envycontrol.rebuild_initramfs()
    assert calls == []


def test_initramfs_failure_is_logged(monkeypatch, caplog):
    monkeypatch.setattr(
        envycontrol.os.path,
        "exists",
        lambda path: path == "/etc/arch-release",
    )
    monkeypatch.setattr(envycontrol.shutil, "which", lambda command: None)
    monkeypatch.setattr(
        envycontrol.subprocess,
        "run",
        lambda args, **kwargs: SimpleNamespace(returncode=1),
    )
    with caplog.at_level(logging.ERROR):
        envycontrol.rebuild_initramfs()
    assert "error ocurred while rebuilding" in caplog.text
