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
class ServiceCfg:
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


class Stack:
    def __init__(self, name: str, args: Config):
        self.name = name

        self.volumes: dict[str, str] = {}
        self.networks: dict[str, str] = {}
        self.services: dict[str, ServiceCfg] = {}
        self.args: Config = args

    def volume(self, name: str):
        self.volumes[name] = name

    def network(self, name: str):
        self.networks[name] = name

    def service(self, cfg: ServiceCfg) -> None:
        self.services[cfg.name] = cfg
