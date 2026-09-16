from hypothesis import given, strategies as st

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


def kinds(result):
    return {evidence.kind for evidence in result.evidence}


def test_arch_dracut_active_with_mkinitcpio_still_installed_detects_dracut():
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

    dracut = boot.DracutBackend().detect(probe)
    mkinitcpio = boot.MkinitcpioBackend().detect(probe)

    assert boot.EvidenceKind.ACTIVE_INTEGRATION in kinds(dracut)
    assert dracut.strongest is boot.EvidenceKind.ACTIVE_INTEGRATION
    assert boot.EvidenceKind.ACTIVE_INTEGRATION not in kinds(mkinitcpio)
    assert mkinitcpio.strongest is boot.EvidenceKind.DISTRO_DEFAULT


def test_dracut_binary_without_configuration_is_only_weak_evidence():
    probe = FakeProbe(commands={"dracut"})

    result = boot.DracutBackend().detect(probe)

    assert result.eligible is True
    assert result.strongest is boot.EvidenceKind.BINARY_PRESENT


def test_arch_active_mkinitcpio_hook_is_strong_evidence():
    probe = FakeProbe(
        paths={
            "/etc/arch-release",
            "/usr/share/libalpm/hooks/90-mkinitcpio-install.hook",
        },
        commands={"mkinitcpio"},
    )

    result = boot.MkinitcpioBackend().detect(probe)

    assert result.strongest is boot.EvidenceKind.ACTIVE_INTEGRATION


def test_booster_configuration_outweighs_binary_presence():
    probe = FakeProbe(
        paths={
            "/etc/arch-release",
            "/etc/booster.yaml",
            "/usr/lib/booster/regenerate_images",
        },
        commands={"booster", "mkinitcpio"},
    )

    result = boot.BoosterBackend().detect(probe)

    assert result.strongest is boot.EvidenceKind.GENERATED_ARTIFACT


def test_empty_dracut_override_disables_packaged_dracut_hook():
    probe = FakeProbe(
        paths={
            "/etc/arch-release",
            "/usr/share/libalpm/hooks/90-dracut-install.hook",
        },
        commands={"dracut"},
        text={"/etc/pacman.d/hooks/90-dracut-install.hook": ""},
    )

    result = boot.DracutBackend().detect(probe)

    assert boot.EvidenceKind.ACTIVE_INTEGRATION not in kinds(result)
    assert result.strongest is boot.EvidenceKind.BINARY_PRESENT


def test_endeavouros_dracut_rebuild_preserves_native_rebuild_command():
    probe = FakeProbe(
        paths={"/usr/lib/endeavouros-release"},
        commands={"dracut", "dracut-rebuild"},
    )

    backend = boot.DracutBackend()

    assert backend.detect(probe).strongest is boot.EvidenceKind.ACTIVE_INTEGRATION
    assert backend.build_command(probe) == ("dracut-rebuild",)


@given(st.lists(st.sampled_from(list(boot.EvidenceKind)), min_size=1, max_size=20))
def test_strongest_evidence_is_always_maximum(kinds_list):
    result = boot.DetectionResult(
        backend="test",
        evidence=tuple(
            boot.DetectionEvidence(kind=kind, description=kind.name)
            for kind in kinds_list
        ),
    )

    assert result.strongest == max(kinds_list)
