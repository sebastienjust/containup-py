from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional, TypedDict, Union

from typing_extensions import NotRequired

from containup.utils.secret_value import SecretValue
from .service_healthcheck import HealthCheck
from .service_mounts import ServiceMounts
from .service_ports import ServicePortMappings

Commands = List[str]

EnvironmentsMapping = Dict[str, Union[str, SecretValue]]


class _RestartPolicy(TypedDict):
    MaximumRetryCount: NotRequired[int]
    Name: NotRequired[Literal["always", "on-failure"]]


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

    container_name: Optional[str] = None
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

    labels: Dict[str, str] = field(default_factory=lambda: {})
    """
    Dictionnary of labels to add to container.
    """

    restart: Optional[_RestartPolicy] = None
    """
    The behavior to apply when the container exits. The default is not to restart.

    An ever increasing delay (double the previous delay, starting at 100ms) 
    is added before each restart to prevent flooding the server.

    Restart the container when it exits. Configured as a dictionary with keys:

    - Name: "no" "always" "unless-stopped" "on-failure".
    - MaximumRetryCount Number of times to restart the container on failure.

    For example: {"Name": "on-failure", "MaximumRetryCount": 5}

    TODO We must improve that, it's awful.
    """

    healthcheck: Optional[HealthCheck] = None
    """Specify a test to perform to check that the container is healthy."""

    depends_on: list[str] = field(default_factory=lambda: [])
    """
    List of services that this container depends on.
    
    Array of strings, each string is a service name.
    Services will be up in this order and down in reverse order.
    
    This is a real depends_on, meaning that if you "up" the stack, 
    we will wait that all dependent services are ready before running this one.
    """

    def mounts_all(self) -> ServiceMounts:
        """Get all volumes and mounts in the same format"""
        return self.volumes + self.mounts

    def container_name_safe(self) -> str:
        """Get container name or service name"""
        return self.container_name or self.name
