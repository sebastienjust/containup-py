import logging
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional, TypedDict, Union

from typing_extensions import NotRequired

from .cli import Config

# TODO get that from elswhere
VERSION = "0.1.0"

# Initialize logger for this lib. Don't force the logger
logger = logging.getLogger(__name__)


class _RestartPolicy(TypedDict):
    MaximumRetryCount: NotRequired[int]
    Name: NotRequired[Literal["always", "on-failure"]]


PortsMapping = Dict[str, int]
EnvironmentsMapping = Dict[str, str]
Volumes = List[str]
Commands = List[str]
HealthCheck = Dict[str, Union[int, str]]


@dataclass
class Service:
    name: str
    image: str
    container_name: str
    ports: PortsMapping = field(default_factory=lambda: {})
    environment: EnvironmentsMapping = field(default_factory=lambda: {})
    volumes: Volumes = field(default_factory=lambda: [])
    network: Optional[str] = None
    command: Commands = field(default_factory=lambda: [])
    restart: Optional[_RestartPolicy] = None
    healthcheck: Optional[Dict[str, Union[int, str]]] = None


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


@dataclass
class Network:

    name: str
    """Name of the network"""

    driver: Optional[str] = None
    """Name of the driver used to create the network"""

    options: Optional[Dict[str, str]] = None
    """Driver options as a key-value dictionary"""


StockItem = Union[Service, Volume, Network]


class Stack:
    def __init__(self, name: str, args: Config):
        self.name = name

        self.volumes: dict[str, Volume] = {}
        self.networks: dict[str, Network] = {}
        self.services: dict[str, Service] = {}
        self.args: Config = args

    def add(self, item_or_list: Union[StockItem, List[StockItem]]):
        items = item_or_list if item_or_list is list else [item_or_list]
        for item in items:
            if isinstance(item, Service):
                self.services[item.name] = item
            elif isinstance(item, Volume):
                self.volumes[item.name] = item
            elif isinstance(item, Network):  # type: ignore
                self.networks[item.name] = item
        return self
