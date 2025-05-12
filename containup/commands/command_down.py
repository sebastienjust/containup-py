import logging
from typing import Optional

import docker

from containup.stack.stack import (
    Stack,
)

logger = logging.getLogger(__name__)


class CommandDown:

    def __init__(self, stack: Stack, client: docker.DockerClient):
        self.stack = stack
        self.client = client

    def down(self, services: Optional[list[str]] = None) -> None:
        targets = (
            self.stack.services
            if not services
            else {k: self.stack.services[k] for k in services}
        )
        for name, cfg in targets.items():
            container_name = cfg.container_name or cfg.name
            try:
                logger.info(f"Remove container {name} : start")
                self.client.containers.get(container_name).remove(force=True)
                logger.info(f"Remove container {name} : done")
            except docker.errors.NotFound:  # type: ignore
                logger.info(f"Remove container {name} : not found")
                continue
