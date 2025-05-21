from abc import ABC, abstractmethod

from containup import Volume, Network, Service
from containup.business.commands.container_health_status import ContainerHealthStatus


class ContainerOperator(ABC):

    @abstractmethod
    def image_exists(self, image: str) -> bool:
        """Checks if image exists

        Arguments:
            image (str) image coordinates
        """
        pass

    @abstractmethod
    def image_pull(self, image: str):
        """Pulls image from remote reposioty

        Arguments:
            image (str) image coordinates
        """
        pass

    @abstractmethod
    def container_exists(self, container_name: str) -> bool:
        """Asks docker if the container exists"""
        pass

    @abstractmethod
    def container_run(self, stack_name: str, service: Service):
        """Runs the service (ie. associated container)"""
        pass

    @abstractmethod
    def container_remove(self, container_name: str):
        """Removes a container"""
        pass

    @abstractmethod
    def container_health_status(self, container_name: str) -> ContainerHealthStatus:
        """Returns status and health of container"""
        pass

    @abstractmethod
    def volume_exists(self, volume_name: str) -> bool:
        """Ensure that the volume exists"""
        pass

    @abstractmethod
    def volume_create(self, stack_name: str, volume: Volume) -> None:
        """Creates the volume"""
        pass

    @abstractmethod
    def network_exists(self, network_name: str) -> bool:
        """Asks docker if the network exists"""
        pass

    @abstractmethod
    def network_create(self, stack_name: str, network: Network) -> None:
        """Creates the network"""
        pass


class ContainerOperatorException(Exception):
    """Custom high-level error for operator failures."""

    pass
