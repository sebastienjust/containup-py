from dataclasses import dataclass
from typing import List, Optional


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


def port(
    container_port: int,
    host_port: Optional[int] = None,
    host_ip: Optional[str] = None,
    protocol: str = "tcp",
) -> ServicePortMapping:
    """
    Shortcut factory to create ServicePortMapping.

    Options and signature are the same as ServicePortMapping class.

    See Also: [ServicePortMapping]
    """
    return ServicePortMapping(container_port, host_port, host_ip, protocol)


ServicePortMappings = List[ServicePortMapping]
