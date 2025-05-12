from dataclasses import dataclass
from typing import Optional


@dataclass
class Volume:
    name: str
    """Name of the volume. If not specified, the engine generates a name."""

    driver: Optional[str] = None
    """Name of the driver used to create the volume"""

    driver_opts: Optional[dict[str, str]] = None
    """Driver options as a key-value dictionary"""

    labels: Optional[dict[str, str]] = None
    """Labels to set on the volume"""
