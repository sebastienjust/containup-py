import logging
import sys
from typing import List, Optional

import docker
from docker.errors import DockerException
from docker.models.volumes import Volume

from containup.infra.docker.healthcheck import (
    healthcheck_to_docker_spec_unsafe,
)
from containup.infra.docker.mounts import mounts_to_docker_specs
from containup.infra.docker.ports import ports_to_docker_spec
from containup.stack.stack import (
    Stack,
)

logger = logging.getLogger(__name__)


class CommandUp:
    def __init__(self, stack: Stack, client: docker.DockerClient):
        self.stack = stack
        self.client = client

    def up(self, services: Optional[List[str]] = None) -> None:
        logger.debug(f"Running command up with services {services}")
        self._ensure_volumes()
        self._ensure_networks()
        targets = (
            self.stack.services.values()
            if not services
            else (self.stack.services[k] for k in services)
        )
        for cfg in targets:
            container_name = cfg.container_name or cfg.name
            try:
                logger.info(f"Remove container if exists {container_name}")
                self.client.containers.get(container_name).remove(force=True)
            except docker.errors.NotFound:  # type: ignore
                pass

            logger.info(f"Run container {container_name} : start")
            try:
                self.client.containers.run(
                    image=cfg.image,
                    command=cfg.command,
                    stdout=True,
                    stderr=False,
                    remove=False,
                    name=container_name,
                    environment=cfg.environment,
                    ports=ports_to_docker_spec(cfg.ports),  # type: ignore
                    mounts=mounts_to_docker_specs(cfg.mounts_all()),
                    network=cfg.network,
                    restart_policy=cfg.restart,
                    detach=True,
                    healthcheck=healthcheck_to_docker_spec_unsafe(cfg.healthcheck),
                )
            except DockerException as e:
                logger.error(f"Run container {container_name} : failed: {e}")
                sys.exit(1)

    def _ensure_volumes(self):
        for vol in self.stack.mounts.values():
            logger.debug(f"Checking {vol.name}")
            if not any(v.name == vol for v in get_docker_volumes(self.client)):
                self.client.volumes.create(  # type: ignore
                    name=vol.name,
                    driver=vol.driver,
                    driver_opts=vol.driver_opts,
                    labels=vol.labels,
                )

    def _ensure_networks(self):
        for net in self.stack.networks.values():
            logger.debug(f"Checking {net.name}")
            try:
                self.client.networks.get(net.name)
            except docker.errors.NotFound:  # type: ignore
                self.client.networks.create(
                    name=net.name, driver=net.driver, options=net.options
                )


def get_docker_volumes(client: docker.DockerClient) -> list[Volume]:
    return client.volumes.list()  # type: ignore[reportUnnecessaryCast]
