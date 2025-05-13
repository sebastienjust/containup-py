import docker
import docker.models
import docker.models.networks
import docker.models.volumes
from docker.errors import DockerException

from containup import Volume, Network, Service
from containup.commands.container_operator import (
    ContainerOperator,
    ContainerOperatorException,
)
from containup.infra.docker.healthcheck import healthcheck_to_docker_spec_unsafe
from containup.infra.docker.mounts import mounts_to_docker_specs
from containup.infra.docker.ports import ports_to_docker_spec


class DockerOperator(ContainerOperator):

    def __init__(self, client: docker.DockerClient):
        self.client = client

    def container_exists(self, container_name: str) -> bool:
        """Asks docker if the container exists"""
        try:
            self.client.containers.get(container_name)
            return True
        except docker.errors.NotFound:  # type: ignore
            return False
        except DockerException as e:
            raise ContainerOperatorException(
                "Failed to check if container {container_name} exists"
            ) from e

    def container_remove(self, container_name: str):
        """Removes a container"""
        try:
            self.client.containers.get(container_name).remove(force=True)
        except DockerException as e:
            raise ContainerOperatorException(
                "Failed to remove container {container_name}"
            ) from e

    def container_run(self, service: Service):
        """Run a container like docker run"""
        container_name = service.container_name or service.name
        try:
            self.client.containers.run(
                image=service.image,
                command=service.command,
                stdout=True,
                stderr=False,
                remove=False,
                name=container_name,
                environment=service.environment,
                ports=ports_to_docker_spec(service.ports),  # type: ignore
                mounts=mounts_to_docker_specs(service.mounts_all()),
                network=service.network,
                restart_policy=service.restart,
                detach=True,
                healthcheck=healthcheck_to_docker_spec_unsafe(service.healthcheck),
            )
        except DockerException as e:
            raise ContainerOperatorException(
                "Failed to run container {container_name} : failed: {e}"
            ) from e

    def volume_exists(self, volume_name: str) -> bool:
        """Asks docker if the volume exists"""
        docker_volumes: list[docker.models.volumes.Volume] = self.client.volumes.list()  # type: ignore
        return any(v.name == volume_name for v in docker_volumes)

    def volume_create(self, volume: Volume) -> None:
        """Creates the volume"""
        self.client.volumes.create(  # type: ignore
            name=volume.name,
            driver=volume.driver,
            driver_opts=volume.driver_opts,
            labels=volume.labels,
        )

    def network_exists(self, network_name: str) -> bool:
        """Asks docker if the network exists"""
        docker_networks: list[docker.models.networks.Network] = self.client.networks.list()  # type: ignore
        return any(net.name == network_name for net in docker_networks)

    def network_create(self, network: Network) -> None:
        """Creates the network"""
        self.client.networks.create(
            name=network.name, driver=network.driver, options=network.options
        )
