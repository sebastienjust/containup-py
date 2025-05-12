import logging
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional, TypedDict, Union

from docker.types import DriverConfig
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

Commands = List[str]
HealthCheck = Dict[str, Union[int, str]]


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


ServiceMounts = List[Union[VolumeMount, BindMount, TmpfsMount]]


@dataclass
class ServicePortMapping:
    """
     Declare a single port mapping for Docker.

    Each mapping corresponds to one container port being exposed on the host.
    You must create one instance per mapping.

    - If you want to bind a specific host port, set `host_port`.
    - If you want to bind on a specific IP address/interface, set `host_ip`.
    - If `host_port` is None, Docker will assign a random free port.
    - If multiple mappings share the same container port, they will all be included.
    - Set `protocol` to 'tcp', 'udp', or 'sctp'. Defaults to 'tcp'.

    Unlike docker-compose; we stick to the most minimal configuration options.
    It means that if you want to open multiple ports, or say, 8080-8090
    you have to do a loop yourself.
    """

    container_port: int
    """The port to expose, inside the container"""

    host_port: Optional[int] = None
    """The port on the host, outside the container. Use None for random port assignment."""

    host_ip: Optional[str] = None
    """
    Optional IP address/interface to bind the port on the host (e.g., '127.0.0.1').
    If None, Docker will listen on all IPs (0.0.0.0)
    """

    protocol: str = "tcp"
    """Protocol for the port mapping. Must be 'tcp', 'udp', or 'sctp'."""


def port(inside: int, outside: Optional[int] = None) -> ServicePortMapping:
    return ServicePortMapping(inside, outside or inside)


ServicePortMappings = List[ServicePortMapping]


@dataclass
class Service:
    """
    Equivalent of a Docker Container's Service.

    Don't be confused, it's **not** a Docker Swarm Service, it is a logical
    representation of your services.
    """

    name: str
    """
    Name to give to the service. It is a logical name, like the one you defined in docker-compose. 
    If you don't define explicitely a container_name, this will be used as the containr name.
    """

    image: str
    """The image name to use for the containers."""

    container_name: Optional[str]
    """Name of the container. If missing, the name of the service will be used."""

    ports: ServicePortMappings = field(default_factory=lambda: [])
    """
    Ports to bind inside the container.

    The keys of the dictionary are the ports to bind inside the container, either as an integer or a string in 
    the form port/protocol, where the protocol is either tcp, udp, or sctp.
    TODO this should be improved
    """

    environment: EnvironmentsMapping = field(default_factory=lambda: {})
    """
    Environment variables to set inside the container, as a dictionary of key/values. For example {"VARIABLE": "10"}.
    
    Even if Docker API accepts a list of strings, we don't want to support ["SOMEVARIABLE=xxx"] syntax
    All keys and values shall be strings. 

    """

    volumes: ServiceMounts = field(default_factory=lambda: [])
    """
    Alias for mounts, same thing, both are merged. 

    We do that because most people know "volumes" and not "mounts"
    """
    mounts: ServiceMounts = field(default_factory=lambda: [])

    """
    List of strings which each one of its elements specifies a mount volume

    example: ['/home/user1/:/mnt/vol2','/var/www:/mnt/vol1']
    TODO this should be improved
    """

    network: Optional[str] = None
    """
    Name of the network this container will be connected to at creation time.

    Incompatible with network_mode (when network_mode will be implemented).
    """

    command: Commands = field(default_factory=lambda: [])
    """
    The command to run in the container. 
    """

    restart: Optional[_RestartPolicy] = None
    """
    Restart the container when it exits. Configured as a dictionary with keys:

    Name One of on-failure, or always.

    MaximumRetryCount Number of times to restart the container on failure.

    For example: {"Name": "on-failure", "MaximumRetryCount": 5}

    TODO We must improve that, it's awful.
    """

    healthcheck: Optional[Dict[str, Union[int, str]]] = None
    """
    Specify a test to perform to check that the container is healthy. The dict takes the following keys:

    test (list or str): Test to perform to determine
    container health. Possible values:

    Empty list: Inherit healthcheck from parent image

    ["NONE"]: Disable healthcheck

    ["CMD", args...]: exec arguments directly.

    ["CMD-SHELL", command]: Run command in the system’s default shell.

    If a string is provided, it will be used as a CMD-SHELL command.

    interval (int): The time to wait between checks in nanoseconds. It should be 0 or at least 1000000 (1 ms).

    timeout (int): The time to wait before considering the check to have hung. It should be 0 or at least 1000000 (1 ms).

    retries (int): The number of consecutive failures needed to
    consider a container as unhealthy.

    start_period (int): Start period for the container to
    initialize before starting health-retries countdown in nanoseconds. It should be 0 or at least 1000000 (1 ms).

    TODO We must improve that, it's awful.
    """

    def mounts_all(self) -> ServiceMounts:
        """Get all volumes and mounts in the same format"""
        return self.volumes + self.mounts


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

        self.mounts: dict[str, Volume] = {}
        self.networks: dict[str, Network] = {}
        self.services: dict[str, Service] = {}
        self.args: Config = args

    def add(self, item_or_list: Union[StockItem, List[StockItem]]):
        items = item_or_list if isinstance(item_or_list, list) else [item_or_list]
        for item in items:
            logger.debug(item)
            if isinstance(item, Service):
                self.services[item.name] = item
            elif isinstance(item, Volume):
                self.mounts[item.name] = item
            elif isinstance(item, Network):  # type: ignore
                self.networks[item.name] = item
        return self
