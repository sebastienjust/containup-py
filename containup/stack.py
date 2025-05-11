import logging

from typing import Optional, TypedDict, NotRequired, Literal
from dataclasses import dataclass, field
from .cli import Config

# TODO get that from elswhere
VERSION = "0.1.0"

# Initialize logger for this lib. Don't force the logger
logger = logging.getLogger(__name__)


class _RestartPolicy(TypedDict):
    MaximumRetryCount: NotRequired[int]
    Name: NotRequired[Literal["always", "on-failure"]]


@dataclass
class ServiceCfg:
    name: str
    image: str
    container_name: str
    ports: dict[str, int] = field(default_factory=dict)
    environment: dict[str, str] = field(default_factory=dict)
    volumes: list[str] = field(default_factory=list)
    network: Optional[str] = None
    command: list[str] = field(default_factory=list)
    restart: Optional[_RestartPolicy] = None
    healthcheck: dict[str, int | str] = field(default_factory=dict)


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



