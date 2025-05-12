from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class Network:

    name: str
    """Name of the network"""

    driver: Optional[str] = None
    """Name of the driver used to create the network"""

    options: Optional[Dict[str, str]] = None
    """Driver options as a key-value dictionary"""
