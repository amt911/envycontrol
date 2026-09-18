import glob
import shutil
import subprocess
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

    def glob(self, pattern: str) -> tuple[Path, ...]: ...


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

    def glob(self, pattern: str) -> tuple[Path, ...]:
        return tuple(Path(path) for path in glob.glob(pattern))


class InitramfsBackend(Protocol):
    name: str

    def detect(self, probe: SystemProbe) -> DetectionResult: ...

    def build_command(self, probe: SystemProbe) -> tuple[str, ...]: ...


class CommandRunner(Protocol):
    def run(self, argv: tuple[str, ...], *, verbose: bool = False) -> CommandResult: ...


class BootArtifactStrategy(Protocol):
    def stages(
        self,
        probe: SystemProbe,
        backend_name: str,
    ) -> tuple["BootStage", ...]: ...


class SubprocessCommandRunner:
    def run(self, argv: tuple[str, ...], *, verbose: bool = False) -> CommandResult:
        if verbose:
            result = subprocess.run(list(argv))
        else:
            result = subprocess.run(
                list(argv),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        return CommandResult(returncode=result.returncode)


@dataclass(frozen=True)
class BootStage:
    name: str
    argv: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.argv:
            raise ValueError("Boot stage command cannot be empty")


@dataclass(frozen=True)
class BootRebuildPlan:
    backend: str
    stages: tuple[BootStage, ...]
    evidence: tuple[DetectionEvidence, ...]
    diagnostics: tuple[str, ...]
    use_inhibit: bool

    def __post_init__(self) -> None:
        if not self.stages:
            raise ValueError("Boot rebuild plan must contain at least one stage")

    def execute(self, runner: CommandRunner, *, verbose: bool = False) -> None:
        for stage in self.stages:
            argv = stage.argv
            if self.use_inhibit:
                argv = (
                    "systemd-inhibit",
                    "--who=envycontrol",
                    "--why",
                    "Rebuilding boot artifacts",
                    "--",
                    *argv,
                )
            result = runner.run(argv, verbose=verbose)
            if result.returncode != 0:
                raise BootRebuildCommandError(
                    f"Boot rebuild stage '{stage.name}' failed for {self.backend}: "
                    + " ".join(stage.argv)
                )


@dataclass(frozen=True)
class KernelInstallConfig:
    layout: str | None = None
    initrd_generator: str | None = None
    uki_generator: str | None = None


class KernelInstallStrategy:
    CONFIG_PATH = "/etc/kernel/install.conf"

    def read_config(self, probe: SystemProbe) -> KernelInstallConfig:
        text = probe.read_text(self.CONFIG_PATH)
        if text is None:
            return KernelInstallConfig()

        values: dict[str, str] = {}
        accepted = {"layout", "initrd_generator", "uki_generator"}
        for raw_line in text.splitlines():
            line = raw_line.split("#", 1)[0].strip()
            if not line or "=" not in line:
                continue
            key, value = (part.strip() for part in line.split("=", 1))
            if key in accepted and value:
                values[key] = value

        return KernelInstallConfig(
            layout=values.get("layout"),
            initrd_generator=values.get("initrd_generator"),
            uki_generator=values.get("uki_generator"),
        )

    def is_authoritative(
        self,
        probe: SystemProbe,
        config: KernelInstallConfig,
    ) -> bool:
        return probe.command_exists("kernel-install") and config.initrd_generator is not None


class NativeBootArtifactStrategy:
    def stages(
        self,
        probe: SystemProbe,
        backend_name: str,
    ) -> tuple[BootStage, ...]:
        return ()


class LimineIntegration:
    CONFIG_PATHS = ("/etc/default/limine", "/etc/limine-entry-tool.conf")
    HOOK_PATTERNS = (
        "/usr/share/libalpm/hooks/*limine*.hook",
        "/etc/pacman.d/hooks/*limine*.hook",
    )

    def validate(
        self,
        probe: SystemProbe,
        *,
        backend_name: str,
    ) -> tuple[BootStage, ...]:
        configured = any(probe.read_text(path) is not None for path in self.CONFIG_PATHS)
        if not configured:
            return ()

        for pattern in self.HOOK_PATTERNS:
            for hook_path in probe.glob(pattern):
                if probe.is_masked(hook_path):
                    continue
                content = probe.read_text(hook_path)
                if not content:
                    continue
                normalized = content.lower()
                if "limine-entry-tool" in normalized and backend_name.lower() in normalized:
                    return ()

        raise UnsupportedBootIntegrationError(
            "Limine configuration was detected, but no supported native "
            f"{backend_name} integration could be verified."
        )


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
                _evidence(
                    EvidenceKind.ACTIVE_INTEGRATION,
                    "EndeavourOS dracut-rebuild integration detected",
                )
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
                _evidence(
                    EvidenceKind.ACTIVE_INTEGRATION,
                    "active mkinitcpio pacman hook detected",
                )
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
                _evidence(
                    EvidenceKind.GENERATED_ARTIFACT,
                    "Booster configuration detected",
                )
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


class BootRebuildCoordinator:
    def __init__(
        self,
        resolver: BootBackendResolver,
        kernel_install: KernelInstallStrategy,
        artifact_strategy: BootArtifactStrategy,
        bootloader_integration: LimineIntegration,
    ):
        self.resolver = resolver
        self.kernel_install = kernel_install
        self.artifact_strategy = artifact_strategy
        self.bootloader_integration = bootloader_integration

    @staticmethod
    def _backend_from_name(name: str) -> InitramfsBackend:
        backends: dict[str, InitramfsBackend] = {
            "dracut": DracutBackend(),
            "mkinitcpio": MkinitcpioBackend(),
            "booster": BoosterBackend(),
        }
        try:
            return backends[name]
        except KeyError as error:
            raise NoBootBackendFoundError(
                f"Unsupported kernel-install initrd_generator={name}"
            ) from error

    @staticmethod
    def _ensure_backend_available(
        backend: InitramfsBackend,
        probe: SystemProbe,
    ) -> None:
        available = {
            "dracut": probe.command_exists("dracut"),
            "mkinitcpio": probe.command_exists("mkinitcpio"),
            "booster": (
                probe.command_exists("booster")
                or probe.exists("/usr/lib/booster/regenerate_images")
            ),
        }.get(backend.name, True)
        if not available:
            raise NoBootBackendFoundError(
                f"kernel-install selects {backend.name}, but its generator is not available"
            )

    def resolve(self, probe: SystemProbe) -> BootRebuildPlan:
        is_ostree = probe.exists("/ostree") or probe.exists("/sysroot/ostree")
        kernel_config = self.kernel_install.read_config(probe)

        if not is_ostree and self.kernel_install.is_authoritative(probe, kernel_config):
            assert kernel_config.initrd_generator is not None
            backend = self._backend_from_name(kernel_config.initrd_generator)
            self._ensure_backend_available(backend, probe)
            evidence = (
                _evidence(
                    EvidenceKind.EXPLICIT_CONFIG,
                    f"kernel-install initrd_generator={kernel_config.initrd_generator}",
                ),
            )
            diagnostics = [evidence[0].description]
            if kernel_config.layout:
                diagnostics.append(f"kernel-install layout={kernel_config.layout}")
            if kernel_config.uki_generator:
                diagnostics.append(
                    f"kernel-install uki_generator={kernel_config.uki_generator}"
                )
            self.bootloader_integration.validate(
                probe,
                backend_name=backend.name,
            )
            return BootRebuildPlan(
                backend=backend.name,
                stages=(BootStage("kernel-install", ("kernel-install", "add-all")),),
                evidence=evidence,
                diagnostics=tuple(diagnostics),
                use_inhibit=probe.command_exists("systemd-inhibit"),
            )

        backend = self.resolver.resolve(probe)
        result = backend.detect(probe)
        artifact_stages = self.artifact_strategy.stages(probe, backend.name)
        bootloader_stages = self.bootloader_integration.validate(
            probe,
            backend_name=backend.name,
        )
        primary = BootStage("initramfs", backend.build_command(probe))
        return BootRebuildPlan(
            backend=backend.name,
            stages=(primary, *artifact_stages, *bootloader_stages),
            evidence=result.evidence,
            diagnostics=tuple(item.description for item in result.evidence),
            use_inhibit=probe.command_exists("systemd-inhibit"),
        )


def default_boot_rebuild_coordinator() -> BootRebuildCoordinator:
    return BootRebuildCoordinator(
        resolver=default_backend_resolver(),
        kernel_install=KernelInstallStrategy(),
        artifact_strategy=NativeBootArtifactStrategy(),
        bootloader_integration=LimineIntegration(),
    )
