from dataclasses import dataclass
from typing import Dict

from containup import Service, Volume, Network
from containup.commands.container_operator import (
    ContainerOperator,
    ContainerOperatorException,
)
from containup.commands.execution_auditor import ExecutionAuditor


class DryRunOperator(ContainerOperator):
    """Operator that does nothing except collecting logs and simulating a fake container operator"""

    def __init__(self, auditor: ExecutionAuditor):
        self._containers: Dict[str, DryRunContainer] = {}
        self._volumes: Dict[str, DryRunVolume] = {}
        self._networks: Dict[str, DryRunNetwork] = {}
        self._auditor = auditor

    def container_exists(self, container_name: str) -> bool:
        result = container_name in self._containers
        self._auditor.record(f"container exists: {container_name}={result}")
        return result

    def container_remove(self, container_name: str):
        try:
            del self._containers[container_name]
            self._auditor.record(f"container removed: {container_name}")
        except KeyError as e:
            raise ContainerOperatorException(
                f"Container {container_name} not found"
            ) from e

    def container_run(self, service: Service):
        container_id: str = service.container_name or service.name
        self._containers[container_id] = DryRunContainer(container_id, service)
        self._auditor.record(f"container run: {service}")

    def volume_exists(self, volume_name: str) -> bool:
        result = volume_name in self._volumes
        self._auditor.record(f"volume exists: {volume_name}={result}")
        return result

    def volume_create(self, volume: Volume) -> None:
        self._auditor.record(f"volume created: {volume.name}")
        self._volumes[volume.name] = DryRunVolume(volume.name, volume)

    def network_exists(self, network_name: str) -> bool:
        result = network_name in self._networks
        self._auditor.record(f"network exists: {network_name}={result}")
        return result

    def network_create(self, network: Network) -> None:
        self._auditor.record(f"network created: {network.name}")
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
