import pytest

import envycontrol_boot as boot


class FakeProbe:
    def __init__(self, *, paths=(), commands=(), text=None):
        self.paths = set(paths)
        self.commands = set(commands)
        self.text = dict(text or {})

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
        return ()


def test_kernel_install_config_parses_explicit_generators_and_comments():
    probe = FakeProbe(
        text={
            "/etc/kernel/install.conf": """
                # managed boot pipeline
                layout = uki
                initrd_generator=dracut
                uki_generator = ukify # compose the UKI
                unknown_key=ignored
            """
        }
    )

    config = boot.KernelInstallStrategy().read_config(probe)

    assert config.layout == "uki"
    assert config.initrd_generator == "dracut"
    assert config.uki_generator == "ukify"


def test_missing_kernel_install_config_returns_empty_config():
    config = boot.KernelInstallStrategy().read_config(FakeProbe())

    assert config == boot.KernelInstallConfig()


def test_explicit_kernel_install_pipeline_runs_once_without_duplicate_ukify():
    probe = FakeProbe(
        paths={"/etc/arch-release"},
        commands={"kernel-install", "dracut", "ukify", "systemd-inhibit"},
        text={
            "/etc/kernel/install.conf": (
                "layout=uki\n"
                "initrd_generator=dracut\n"
                "uki_generator=ukify\n"
            )
        },
    )

    plan = boot.default_boot_rebuild_coordinator().resolve(probe)

    assert plan.backend == "dracut"
    assert [stage.argv for stage in plan.stages] == [("kernel-install", "add-all")]
    assert all("ukify" not in stage.argv for stage in plan.stages)
    assert plan.use_inhibit is True


def test_unsupported_explicit_kernel_install_generator_fails_closed():
    probe = FakeProbe(
        commands={"kernel-install"},
        text={"/etc/kernel/install.conf": "initrd_generator=custom-tool\n"},
    )

    with pytest.raises(boot.NoBootBackendFoundError, match="custom-tool"):
        boot.default_boot_rebuild_coordinator().resolve(probe)
