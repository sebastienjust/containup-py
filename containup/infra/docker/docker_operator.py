from typing import Optional

import docker
import docker.models
import docker.models.networks
import docker.models.volumes

from docker.errors import DockerException
from docker.models.containers import Container

from containup import NoneHealthcheck, HealthcheckOptions
from containup.stack.volume import Volume
from containup.stack.network import Network
from containup.stack.stack import Service
from containup.utils.duration_to_nano import duration_to_seconds
from containup.utils.secret_value import SecretValue
from containup.commands.container_operator import (
    ContainerOperator,
    ContainerOperatorException,
)
from containup.infra.docker.healthcheck import healthcheck_to_docker_spec_unsafe
from containup.infra.docker.mounts import mounts_to_docker_specs
from containup.infra.docker.ports import ports_to_docker_spec
import time

import logging

logger = logging.getLogger(__name__)


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

    def container_run(self, service: Service):
        """Run a container like docker run"""
        container_name = service.container_name or service.name

        # time to reveal secrects, no other way is possible to give them to docker
        env = {
            key: value.reveal() if isinstance(value, SecretValue) else value
            for key, value in service.environment.items()
        }

        try:
            self.client.containers.run(
                image=service.image,
                command=service.command,
                stdout=True,
                stderr=False,
                remove=False,
                name=container_name,
                environment=env,
                ports=ports_to_docker_spec(service.ports),  # type: ignore
                mounts=mounts_to_docker_specs(service.mounts_all()),
                network=service.network,
                labels=service.labels,
                restart_policy=service.restart,
                detach=True,
                healthcheck=healthcheck_to_docker_spec_unsafe(service.healthcheck),
            )
        except DockerException as e:
            raise ContainerOperatorException(
                f"Failed to run container {container_name} : {e}"
            ) from e

    def container_wait_healthy(self, service: Service) -> None:
        healthcheck = service.healthcheck
        if healthcheck is None or isinstance(healthcheck, NoneHealthcheck):
            return
        options = getattr(service.healthcheck, "options", None)
        opts: HealthcheckOptions = options or HealthcheckOptions()
        interval: float = duration_to_seconds(opts.interval or "1s")
        timeout: float = duration_to_seconds(opts.timeout or "30s")
        retries: int = opts.retries or 3
        start_period: float = duration_to_seconds(opts.start_period or "1s")
        start_interval: float = duration_to_seconds(opts.start_interval or "1s")
        max_attempts: int = retries + 1

        deadline: float = (
            time.time() + timeout * retries * interval + start_period + start_interval
        )
        attempt: int = 0

        container_name = service.container_name_safe()

        logger.info(
            f"Wait container {container_name} plan. Interval: {interval} timeout: {timeout} retries: {retries}"
        )

        try:
            container: Container = self.client.containers.get(container_name)
            while time.time() < deadline and attempt < max_attempts:
                container.reload()
                state: dict[str, str] = container.attrs.get("State", {})
                health: Optional[str] = state.get("Health", {}).get("Status")  # type: ignore
                status: Optional[str] = state.get("Status")  # type: ignore
                logger.info(
                    f"Wait container {container_name} attempts: {attempt}/{max_attempts} status: {status} health: {health}"
                )
                if status == "exited":
                    raise ContainerOperatorException(
                        f"Container {container_name} exited before becoming healthy."
                    )

                if health == "healthy":
                    return

                if health == "unhealthy":
                    attempt += 1

                time.sleep(interval)

            raise ContainerOperatorException(
                f"Container {container_name} did not become healthy in time."
            )

        except DockerException as e:
            raise ContainerOperatorException(
                f"Failed to get health status for container {container_name}: {e}"
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
