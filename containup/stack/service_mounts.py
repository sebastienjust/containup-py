from dataclasses import dataclass
from typing import List, Optional, Union
from docker.types import DriverConfig


@dataclass
class BindMount:
    """
    Represents a Docker 'bind' mount (host directory mounted into the container).
    """

    source: str
    """Absolute path on the host to mount."""

    target: str
    """Path inside the container where the bind will be mounted."""

    read_only: bool = False
    """If True, mount is read-only."""

    consistency: Optional[str] = None
    """Mount consistency mode ('default', 'consistent', 'cached', 'delegated')."""

    propagation: Optional[str] = None
    """Mount propagation mode with the value [r]private, [r]shared, or [r]slave."""


@dataclass
class VolumeMount:
    """Represents a Docker volume mount."""

    source: str
    """Name of the Docker volume."""

    target: str
    """Path inside the container where the volume will be mounted."""

    read_only: bool = False
    """If True, volume is mounted read-only."""

    consistency: Optional[str] = None
    """Mount consistency mode ('default', 'consistent', 'cached', 'delegated')."""

    no_copy: bool = False
    """False if the volume should be populated with the data from the target. Default: False."""

    labels: Optional[dict[str, str]] = None
    """Labels to set on the volume"""

    driver_config: Optional[DriverConfig] = None
    """Name and configuration of the driver used to create the volume."""


@dataclass
class TmpfsMount:
    """
    Represents a Docker tmpfs mount (in-memory filesystem).
    """

    target: str
    """Path inside the container where the tmpfs will be mounted."""

    read_only: bool = False
    """If True, tmpfs is mounted read-only."""

    consistency: Optional[str] = None
    """Mount consistency mode ('default', 'consistent', 'cached', 'delegated')."""

    tmpfs_size: Optional[Union[int, str]] = None
    """Size of the tmpfs mount (in bytes or as a string like '64m')."""

    tmpfs_mode: Optional[int] = None
    """Filesystem permission mode (e.g., 1777)."""


ServiceMount = Union[VolumeMount, BindMount, TmpfsMount]
ServiceMounts = List[ServiceMount]
