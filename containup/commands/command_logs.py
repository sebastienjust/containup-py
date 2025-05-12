import logging

import docker

from containup.stack.stack import Stack

logger = logging.getLogger(__name__)


class CommandLogs:
    def __init__(self, stack: Stack, client: docker.DockerClient):
        self.stack = stack
        self.client = client

    def logs(self, service: str) -> None:
        cfg = self.stack.services[service]
        container_name = cfg.container_name or cfg.name
        try:
            container = self.client.containers.get(container_name)
            logs = container.logs(stream=False)
            logger.info(logs.decode())
        except docker.errors.NotFound:  # type: ignore
            logger.error(
                f"Service '{service}', container {container_name} is not running."
            )
