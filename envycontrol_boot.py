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
