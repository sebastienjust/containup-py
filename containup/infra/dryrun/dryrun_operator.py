from dataclasses import dataclass
from typing import Dict

from containup import Service, Volume, Network
from containup.business.commands.container_health_status import ContainerHealthStatus
from containup.business.commands.container_operator import (
    ContainerOperator,
    ContainerOperatorException,
)
from containup.business.execution_listener import (
    ExecutionListener,
)


class DryRunOperator(ContainerOperator):
    """Operator that does nothing. Used as a safety guard when using the dry-run mode"""

    def __init__(self, auditor: ExecutionListener):
        self._containers: Dict[str, DryRunContainer] = {}
        self._volumes: Dict[str, DryRunVolume] = {}
        self._networks: Dict[str, DryRunNetwork] = {}
        self._images: list[str] = []
        self._auditor = auditor

    def image_exists(self, image: str):
        exists: bool = image in self._images

        return exists

    def image_pull(self, image: str):
        pass

    def container_exists(self, container_name: str) -> bool:
        result = container_name in self._containers

        return result

    def container_remove(self, container_name: str):
        try:
            del self._containers[container_name]

        except KeyError as e:
            raise ContainerOperatorException(
                f"Container {container_name} not found"
            ) from e

    def container_run(self, stack_name: str, service: Service):
        container_id: str = service.container_name or service.name
        self._containers[container_id] = DryRunContainer(container_id, service)

    def container_health_status(self, container_name: str) -> ContainerHealthStatus:
        return ContainerHealthStatus("running", "healthy")

    def volume_exists(self, volume_name: str) -> bool:
        result = volume_name in self._volumes
        return result

    def volume_create(self, stack_name: str, volume: Volume) -> None:
        self._volumes[volume.name] = DryRunVolume(volume.name, volume)

    def network_exists(self, network_name: str) -> bool:
        result = network_name in self._networks
        return result

    def network_create(self, stack_name: str, network: Network) -> None:
        self._networks[network.name] = DryRunNetwork(network.name, network)


@dataclass
class DryRunContainer:
    container_id: str
    service: Service


@dataclass
class DryRunVolume:
    volume_id: str
    service: Volume


@dataclass
class DryRunNetwork:
    network_id: str
    service: Network
