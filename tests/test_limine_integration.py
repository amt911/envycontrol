import pytest

import envycontrol_boot as boot


class FakeProbe:
    def __init__(self, *, paths=(), commands=(), text=None, globbed=None):
        self.paths = set(paths)
        self.commands = set(commands)
        self.text = dict(text or {})
        self.globbed = dict(globbed or {})

    def exists(self, path):
        key = str(path)
        return key in self.paths or key in self.text

    def is_file(self, path):
        return self.exists(path)

    def is_masked(self, path):
        return False

    def command_exists(self, name):
        return name in self.commands

    def read_text(self, path):
        return self.text.get(str(path))

    def glob(self, pattern):
        return tuple(self.globbed.get(pattern, ()))


def test_no_limine_configuration_requires_no_integration_stage():
    integration = boot.LimineIntegration()

    assert integration.validate(FakeProbe(), backend_name="dracut") == ()


def test_known_dracut_limine_hook_is_treated_as_native_and_not_duplicated():
    hook = "/usr/share/libalpm/hooks/90-limine-dracut.hook"
    probe = FakeProbe(
        commands={"limine-entry-tool"},
        text={
            "/etc/default/limine": "ESP_PATH=/efi\n",
            hook: "Exec = /usr/bin/limine-entry-tool dracut\n",
        },
        globbed={"/usr/share/libalpm/hooks/*limine*.hook": (hook,)},
    )

    stages = boot.LimineIntegration().validate(probe, backend_name="dracut")

    assert stages == ()


def test_known_mkinitcpio_limine_hook_is_treated_as_native_and_not_duplicated():
    hook = "/etc/pacman.d/hooks/90-limine-mkinitcpio.hook"
    probe = FakeProbe(
        commands={"limine-entry-tool"},
        text={
            "/etc/default/limine": "ESP_PATH=/efi\n",
            hook: "Exec = /usr/bin/limine-entry-tool mkinitcpio\n",
        },
        globbed={"/etc/pacman.d/hooks/*limine*.hook": (hook,)},
    )

    stages = boot.LimineIntegration().validate(probe, backend_name="mkinitcpio")

    assert stages == ()


def test_manual_limine_configuration_without_known_native_hook_fails_preflight():
    probe = FakeProbe(
        commands={"limine-entry-tool"},
        text={"/etc/default/limine": "ESP_PATH=/efi\n"},
    )

    with pytest.raises(boot.UnsupportedBootIntegrationError, match="Limine"):
        boot.LimineIntegration().validate(probe, backend_name="dracut")
