from pathlib import Path

import envycontrol_boot as boot


class NullProbe:
    def exists(self, path):
        return False

    def is_file(self, path):
        return False

    def is_masked(self, path):
        return False

    def command_exists(self, name):
        return False

    def read_text(self, path):
        return None


def test_backend_commands_preserve_supported_rebuild_contracts():
    probe = NullProbe()

    assert boot.RpmOstreeBackend().build_command(probe) == (
        "rpm-ostree",
        "initramfs",
        "--enable",
        "--arg=--force",
    )
    assert boot.UpdateInitramfsBackend().build_command(probe) == (
        "update-initramfs",
        "-u",
        "-k",
        "all",
    )
    assert boot.DracutBackend().build_command(probe) == (
        "dracut",
        "-f",
        "--regenerate-all",
    )
    assert boot.MakeInitrdBackend().build_command(probe) == ("make-initrd",)
    assert boot.MkinitcpioBackend().build_command(probe) == ("mkinitcpio", "-P")
    assert boot.BoosterBackend().build_command(probe) == (
        "/usr/lib/booster/regenerate_images",
    )


def test_backend_names_are_stable_and_unique():
    backends = (
        boot.RpmOstreeBackend(),
        boot.UpdateInitramfsBackend(),
        boot.DracutBackend(),
        boot.MakeInitrdBackend(),
        boot.MkinitcpioBackend(),
        boot.BoosterBackend(),
    )

    names = [backend.name for backend in backends]
    assert names == [
        "rpm-ostree",
        "update-initramfs",
        "dracut",
        "make-initrd",
        "mkinitcpio",
        "booster",
    ]
    assert len(names) == len(set(names))


def test_setup_packages_boot_runtime_module():
    setup_text = Path("setup.py").read_text(encoding="utf-8")
    assert "py_modules=['envycontrol', 'envycontrol_boot']" in setup_text
