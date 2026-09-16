import pytest

import envycontrol_boot as boot


class FakeProbe:
    def __init__(self, *, paths=(), commands=(), masked=(), text=None):
        self.paths = set(paths)
        self.commands = set(commands)
        self.masked = set(masked)
        self.text = dict(text or {})

    def exists(self, path):
        key = str(path)
        return key in self.paths or key in self.masked or key in self.text

    def is_file(self, path):
        return self.exists(path)

    def is_masked(self, path):
        return str(path) in self.masked

    def command_exists(self, name):
        return name in self.commands

    def read_text(self, path):
        return self.text.get(str(path))


class FakeBackend:
    def __init__(self, name, strongest=None):
        self.name = name
        self._strongest = strongest

    def detect(self, probe):
        evidence = ()
        if self._strongest is not None:
            evidence = (boot.DetectionEvidence(self._strongest, f"{self.name} evidence"),)
        return boot.DetectionResult(self.name, evidence, eligible=bool(evidence))

    def build_command(self, probe):
        return (self.name,)


def test_unique_strongest_candidate_wins():
    resolver = boot.BootBackendResolver(
        backends=(
            FakeBackend("mkinitcpio", boot.EvidenceKind.DISTRO_DEFAULT),
            FakeBackend("dracut", boot.EvidenceKind.ACTIVE_INTEGRATION),
        )
    )

    assert resolver.resolve(FakeProbe()).name == "dracut"


def test_equal_authoritative_candidates_are_rejected_as_ambiguous():
    resolver = boot.BootBackendResolver(
        backends=(
            FakeBackend("mkinitcpio", boot.EvidenceKind.ACTIVE_INTEGRATION),
            FakeBackend("dracut", boot.EvidenceKind.ACTIVE_INTEGRATION),
        )
    )

    with pytest.raises(boot.AmbiguousBootBackendError) as error:
        resolver.resolve(FakeProbe())

    assert "mkinitcpio" in str(error.value)
    assert "dracut" in str(error.value)


def test_no_detected_backend_is_an_explicit_error():
    resolver = boot.BootBackendResolver(backends=(FakeBackend("none"),))

    with pytest.raises(boot.NoBootBackendFoundError):
        resolver.resolve(FakeProbe())


def test_arch_dracut_configuration_beats_mkinitcpio_default():
    probe = FakeProbe(
        paths={
            "/etc/arch-release",
            "/usr/share/libalpm/hooks/90-dracut-install.hook",
        },
        commands={"dracut", "mkinitcpio"},
        masked={
            "/etc/pacman.d/hooks/90-mkinitcpio-install.hook",
            "/etc/pacman.d/hooks/60-mkinitcpio-remove.hook",
        },
    )

    assert boot.default_backend_resolver().resolve(probe).name == "dracut"


def test_arch_mkinitcpio_active_hook_selects_mkinitcpio():
    probe = FakeProbe(
        paths={
            "/etc/arch-release",
            "/usr/share/libalpm/hooks/90-mkinitcpio-install.hook",
        },
        commands={"mkinitcpio"},
    )

    assert boot.default_backend_resolver().resolve(probe).name == "mkinitcpio"


def test_arch_booster_configuration_selects_booster_over_mkinitcpio_default():
    probe = FakeProbe(
        paths={
            "/etc/arch-release",
            "/etc/booster.yaml",
            "/usr/lib/booster/regenerate_images",
        },
        commands={"booster", "mkinitcpio"},
    )

    assert boot.default_backend_resolver().resolve(probe).name == "booster"


@pytest.mark.parametrize(
    ("paths", "commands", "expected"),
    [
        ({"/ostree"}, {"rpm-ostree"}, "rpm-ostree"),
        ({"/sysroot/ostree"}, {"rpm-ostree"}, "rpm-ostree"),
        ({"/etc/debian_version"}, {"update-initramfs"}, "update-initramfs"),
        ({"/etc/redhat-release"}, {"dracut"}, "dracut"),
        ({"/usr/bin/zypper"}, {"dracut"}, "dracut"),
        ({"/etc/altlinux-release"}, {"make-initrd"}, "make-initrd"),
    ],
)
def test_default_resolver_preserves_existing_distribution_backends(paths, commands, expected):
    probe = FakeProbe(paths=paths, commands=commands)

    assert boot.default_backend_resolver().resolve(probe).name == expected
