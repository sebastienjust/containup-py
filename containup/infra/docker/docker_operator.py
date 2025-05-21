import logging
from typing import Optional, Tuple, cast

import docker
import docker.models
import docker.models.networks
import docker.models.volumes

from docker.utils import parse_repository_tag  # type: ignore
from docker.errors import DockerException, ImageNotFound
from docker.models.containers import Container

from containup.business.commands.container_health_status import ContainerHealthStatus
from containup.business.commands.container_operator import (
    ContainerOperator,
    ContainerOperatorException,
)
from containup.business.commands.user_interactions import UserInteractions
from containup.infra.docker.healthcheck import healthcheck_to_docker_spec_unsafe
from containup.infra.docker.mounts import mounts_to_docker_specs
from containup.infra.docker.ports import ports_to_docker_spec
from containup.stack.network import Network
from containup.stack.stack import Service
from containup.stack.volume import Volume
from containup.utils.secret_value import SecretValue

logger = logging.getLogger(__name__)


class DockerOperator(ContainerOperator):

    def __init__(
        self, client: docker.DockerClient, system_interactions: UserInteractions
    ):
        self.client = client
        self._system_interactions = system_interactions

    def image_exists(self, image: str) -> bool:
        try:
            (repository, image_tag) = cast(Tuple[str, str], parse_repository_tag(image))
            tag = image_tag or "latest"  # type: ignore
            exists = False
            try:
                self.client.images.get(image)
                logger.debug(f"Image {repository}:{tag} already downloaded.")
                exists = True
            except ImageNotFound:
                exists = False
                logger.debug(f"Image {repository}:{tag} not yet downloaded.")
                pass
        except DockerException as e:
            raise ContainerOperatorException(
                "Can not check if image [{image}] exists : {e}"
            ) from e
        return exists

    def image_pull(self, image: str):
        try:
            (repository, image_tag) = cast(Tuple[str, str], parse_repository_tag(image))
            tag = image_tag or "latest"  # type: ignore
            logger.info(f"Image {repository}:{tag} pulling image")
            pull_log = self.client.api.pull(  # type: ignore
                repository, tag=tag, stream=True, all_tags=False, decode=True
            )  # type: ignore
            for log in pull_log:  # type: ignore
                logger.info((log.get("status") or "unknown status") + " " + (log.get("progress") or ""))  # type: ignore
        except DockerException as e:
            raise ContainerOperatorException(
                "Can not pull image [{image}] : {e}"
            ) from e

    def container_exists(self, container_name: str) -> bool:
        """Asks docker if the container exists"""
        try:
            self.client.containers.get(container_name)
            return True
        except docker.errors.NotFound:  # type: ignore
            return False
        except DockerException as e:
            raise ContainerOperatorException(
                f"Failed to check if container {container_name} exists: {e}"
            ) from e

    def container_remove(self, container_name: str):
        """Removes a container"""
        try:
            self.client.containers.get(container_name).remove(force=True)
        except DockerException as e:
            raise ContainerOperatorException(
                f"Failed to remove container {container_name}: {e}"
            ) from e

    def container_run(self, stack_name: str, service: Service):
        """Run a container like docker run"""
        container_name = service.container_name or service.name

        try:

            # time to reveal secrects, no other way is possible to give them to docker
            env = {
                key: value.reveal() if isinstance(value, SecretValue) else value
                for key, value in service.environment.items()
            }

            # create the container
            logger.info(f"Container {container_name}: create")
            container = self.client.containers.create(  # type: ignore
                image=service.image,
                command=service.command,
                name=container_name,
                environment=env,
                ports=ports_to_docker_spec(service.ports),  # type: ignore
                mounts=mounts_to_docker_specs(service.mounts_all()),
                network=service.network,
                labels=make_labels(stack_name, service.labels),
                restart_policy=service.restart,
                detach=True,
                healthcheck=healthcheck_to_docker_spec_unsafe(service.healthcheck),
            )

            logger.info(f"Container {container_name}: starting")
            container.start()
            logger.info(f"Container {container_name}: launched")

        except DockerException as e:
            raise ContainerOperatorException(
                f"Failed to run container {container_name} : {e}"
            ) from e

    def container_health_status(self, container_name: str) -> ContainerHealthStatus:
        container: Container = self.client.containers.get(container_name)
        container.reload()
        state: dict[str, str] = container.attrs.get("State", {})
        health: str = str(state.get("Health", {}).get("Status") or "unknown")  # type: ignore
        status: str = str(state.get("Status") or "unknown")  # type: ignore
        return ContainerHealthStatus(status, health)

    def volume_exists(self, volume_name: str) -> bool:
        """Asks docker if the volume exists"""
        docker_volumes: list[docker.models.volumes.Volume] = self.client.volumes.list()  # type: ignore
        return any(v.name == volume_name for v in docker_volumes)

    def volume_create(self, stack_name: str, volume: Volume) -> None:
        """Creates the volume"""
        self.client.volumes.create(  # type: ignore
            name=volume.name,
            driver=volume.driver,
            driver_opts=volume.driver_opts,
            labels=make_labels(stack_name, volume.labels),
        )

    def network_exists(self, network_name: str) -> bool:
        """Asks docker if the network exists"""
        docker_networks: list[docker.models.networks.Network] = self.client.networks.list()  # type: ignore
        return any(net.name == network_name for net in docker_networks)

    def network_create(self, stack_name: str, network: Network) -> None:
        """Creates the network"""
        self.client.networks.create(
            name=network.name,
            driver=network.driver,
            options=network.options,
            labels=make_labels(stack_name, None),
        )


def make_labels(stack_name: str, labels: Optional[dict[str, str]]) -> dict[str, str]:
    return {
        **(labels or {}),
        "com.docker.compose.project": stack_name,
        "containup.stack.name": stack_name,
    }
