import shutil
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import Protocol


class EvidenceKind(IntEnum):
    BINARY_PRESENT = 1
    DISTRO_DEFAULT = 2
    GENERATED_ARTIFACT = 3
    ACTIVE_INTEGRATION = 4
    EXPLICIT_CONFIG = 5


@dataclass(frozen=True)
class DetectionEvidence:
    kind: EvidenceKind
    description: str


@dataclass(frozen=True)
class DetectionResult:
    backend: str
    evidence: tuple[DetectionEvidence, ...]
    eligible: bool = True

    @property
    def strongest(self) -> EvidenceKind:
        return max(
            (item.kind for item in self.evidence),
            default=EvidenceKind.BINARY_PRESENT,
        )


@dataclass(frozen=True)
class CommandResult:
    returncode: int


class SystemProbe(Protocol):
    def exists(self, path: Path | str) -> bool: ...

    def is_file(self, path: Path | str) -> bool: ...

    def is_masked(self, path: Path | str) -> bool: ...

    def command_exists(self, name: str) -> bool: ...

    def read_text(self, path: Path | str) -> str | None: ...


class LocalSystemProbe:
    def exists(self, path: Path | str) -> bool:
        return Path(path).exists()

    def is_file(self, path: Path | str) -> bool:
        return Path(path).is_file()

    def is_masked(self, path: Path | str) -> bool:
        candidate = Path(path)
        if not candidate.is_symlink():
            return False
        try:
            return candidate.resolve() == Path("/dev/null")
        except OSError:
            return False

    def command_exists(self, name: str) -> bool:
        return shutil.which(name) is not None

    def read_text(self, path: Path | str) -> str | None:
        try:
            return Path(path).read_text(encoding="utf-8")
        except OSError:
            return None


class InitramfsBackend(Protocol):
    name: str

    def detect(self, probe: SystemProbe) -> DetectionResult: ...

    def build_command(self, probe: SystemProbe) -> tuple[str, ...]: ...


def _evidence(kind: EvidenceKind, description: str) -> DetectionEvidence:
    return DetectionEvidence(kind=kind, description=description)


def _active_hook(
    probe: SystemProbe,
    packaged_path: str,
    override_path: str,
) -> bool:
    if probe.is_masked(override_path):
        return False
    if probe.exists(override_path):
        override = probe.read_text(override_path)
        return bool(override and override.strip())
    return probe.exists(packaged_path)


class _BaseBackend:
    name = ""

    def _result(self, evidence: list[DetectionEvidence]) -> DetectionResult:
        return DetectionResult(self.name, tuple(evidence), eligible=bool(evidence))

    def detect(self, probe: SystemProbe) -> DetectionResult:
        return self._result([])


class RpmOstreeBackend(_BaseBackend):
    name = "rpm-ostree"

    def detect(self, probe: SystemProbe) -> DetectionResult:
        evidence = []
        if (
            probe.command_exists("rpm-ostree")
            and (probe.exists("/ostree") or probe.exists("/sysroot/ostree"))
        ):
            evidence.append(
                _evidence(EvidenceKind.EXPLICIT_CONFIG, "rpm-ostree system detected")
            )
        return self._result(evidence)

    def build_command(self, probe: SystemProbe) -> tuple[str, ...]:
        return ("rpm-ostree", "initramfs", "--enable", "--arg=--force")


class UpdateInitramfsBackend(_BaseBackend):
    name = "update-initramfs"

    def detect(self, probe: SystemProbe) -> DetectionResult:
        evidence = []
        if probe.command_exists("update-initramfs") and probe.exists("/etc/debian_version"):
            evidence.append(
                _evidence(EvidenceKind.DISTRO_DEFAULT, "Debian-family system detected")
            )
        return self._result(evidence)

    def build_command(self, probe: SystemProbe) -> tuple[str, ...]:
        return ("update-initramfs", "-u", "-k", "all")


class DracutBackend(_BaseBackend):
    name = "dracut"

    def detect(self, probe: SystemProbe) -> DetectionResult:
        evidence = []
        if probe.command_exists("dracut"):
            evidence.append(_evidence(EvidenceKind.BINARY_PRESENT, "dracut is installed"))

        if (
            probe.command_exists("dracut")
            and (probe.exists("/etc/redhat-release") or probe.exists("/usr/bin/zypper"))
        ):
            evidence.append(
                _evidence(EvidenceKind.DISTRO_DEFAULT, "distribution uses dracut by default")
            )

        if probe.command_exists("dracut") and (
            probe.exists("/etc/dracut.conf") or probe.exists("/etc/dracut.conf.d")
        ):
            evidence.append(
                _evidence(EvidenceKind.GENERATED_ARTIFACT, "dracut configuration detected")
            )

        if probe.command_exists("dracut") and _active_hook(
            probe,
            "/usr/share/libalpm/hooks/90-dracut-install.hook",
            "/etc/pacman.d/hooks/90-dracut-install.hook",
        ):
            evidence.append(
                _evidence(EvidenceKind.ACTIVE_INTEGRATION, "active dracut pacman hook detected")
            )

        if (
            probe.exists("/usr/lib/endeavouros-release")
            and probe.command_exists("dracut")
            and probe.command_exists("dracut-rebuild")
        ):
            evidence.append(
                _evidence(EvidenceKind.ACTIVE_INTEGRATION, "EndeavourOS dracut-rebuild integration detected")
            )

        return self._result(evidence)

    def build_command(self, probe: SystemProbe) -> tuple[str, ...]:
        if (
            probe.exists("/usr/lib/endeavouros-release")
            and probe.command_exists("dracut-rebuild")
        ):
            return ("dracut-rebuild",)
        return ("dracut", "-f", "--regenerate-all")


class MakeInitrdBackend(_BaseBackend):
    name = "make-initrd"

    def detect(self, probe: SystemProbe) -> DetectionResult:
        evidence = []
        if probe.command_exists("make-initrd") and probe.exists("/etc/altlinux-release"):
            evidence.append(
                _evidence(EvidenceKind.DISTRO_DEFAULT, "ALT Linux system detected")
            )
        return self._result(evidence)

    def build_command(self, probe: SystemProbe) -> tuple[str, ...]:
        return ("make-initrd",)


class MkinitcpioBackend(_BaseBackend):
    name = "mkinitcpio"

    def detect(self, probe: SystemProbe) -> DetectionResult:
        evidence = []
        if probe.command_exists("mkinitcpio"):
            evidence.append(
                _evidence(EvidenceKind.BINARY_PRESENT, "mkinitcpio is installed")
            )

        if probe.command_exists("mkinitcpio") and probe.exists("/etc/arch-release"):
            evidence.append(
                _evidence(EvidenceKind.DISTRO_DEFAULT, "Arch mkinitcpio default")
            )

        if probe.command_exists("mkinitcpio") and _active_hook(
            probe,
            "/usr/share/libalpm/hooks/90-mkinitcpio-install.hook",
            "/etc/pacman.d/hooks/90-mkinitcpio-install.hook",
        ):
            evidence.append(
                _evidence(EvidenceKind.ACTIVE_INTEGRATION, "active mkinitcpio pacman hook detected")
            )

        return self._result(evidence)

    def build_command(self, probe: SystemProbe) -> tuple[str, ...]:
        return ("mkinitcpio", "-P")


class BoosterBackend(_BaseBackend):
    name = "booster"

    def detect(self, probe: SystemProbe) -> DetectionResult:
        evidence = []
        helper_exists = probe.exists("/usr/lib/booster/regenerate_images")
        if probe.command_exists("booster") or helper_exists:
            evidence.append(_evidence(EvidenceKind.BINARY_PRESENT, "Booster is installed"))

        if helper_exists and probe.exists("/etc/booster.yaml"):
            evidence.append(
                _evidence(EvidenceKind.GENERATED_ARTIFACT, "Booster configuration detected")
            )

        return self._result(evidence)

    def build_command(self, probe: SystemProbe) -> tuple[str, ...]:
        return ("/usr/lib/booster/regenerate_images",)


class BootRebuildError(RuntimeError):
    pass


class NoBootBackendFoundError(BootRebuildError):
    pass


class AmbiguousBootBackendError(BootRebuildError):
    pass


class UnsupportedBootIntegrationError(BootRebuildError):
    pass


class BootRebuildCommandError(BootRebuildError):
    pass


class BootBackendResolver:
    def __init__(self, backends: tuple[InitramfsBackend, ...]):
        self.backends = backends

    def resolve(self, probe: SystemProbe) -> InitramfsBackend:
        detected = []
        for backend in self.backends:
            result = backend.detect(probe)
            if result.eligible and result.evidence:
                detected.append((backend, result))

        if not detected:
            raise NoBootBackendFoundError(
                "No supported initramfs generator could be detected from the current configuration."
            )

        strongest = max(result.strongest for _, result in detected)
        winners = [
            (backend, result)
            for backend, result in detected
            if result.strongest == strongest
        ]

        if len(winners) != 1:
            details = "; ".join(
                f"{backend.name}: "
                + ", ".join(item.description for item in result.evidence)
                for backend, result in winners
            )
            raise AmbiguousBootBackendError(
                f"Multiple boot rebuild backends have equally strong evidence: {details}"
            )

        return winners[0][0]


def default_backend_resolver() -> BootBackendResolver:
    return BootBackendResolver(
        backends=(
            RpmOstreeBackend(),
            UpdateInitramfsBackend(),
            DracutBackend(),
            MakeInitrdBackend(),
            MkinitcpioBackend(),
            BoosterBackend(),
        )
    )
