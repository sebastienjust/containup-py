import logging
from typing import List, Optional

import docker

from containup.commands.container_operator import (
    ContainerOperator,
    ContainerOperatorException,
)
from containup.commands.user_interactions import UserInteractions
from containup.stack.stack import (
    Stack,
)

logger = logging.getLogger(__name__)


class CommandUp:
    def __init__(
        self,
        stack: Stack,
        client: docker.DockerClient,
        operator: ContainerOperator,
        user_interactions: UserInteractions,
    ):
        self.stack = stack
        self.client = client
        self.operator = operator
        self.user_interactions = user_interactions

    def up(self, services: Optional[List[str]] = None) -> None:
        try:
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

                if self.operator.container_exists(container_name):
                    logger.info(f"Container {container_name} exists... removing")
                    self.operator.container_remove(container_name)
                else:
                    logger.info(f"Container {container_name} doesn't exist")

                logger.info(f"Run container {container_name} : start")
                self.operator.container_run(cfg)
                logger.info(f"Run container {container_name} : start done")

        except ContainerOperatorException as e:
            logger.error(f"Command up failed: {e}")
            self.user_interactions.exit_with_error(1)

    def _ensure_volumes(self):
        for vol in self.stack.mounts.values():
            logger.debug(f"Volume {vol.name}: checking if exists")
            if not self.operator.volume_exists(vol.name):
                logger.debug(f"Volume {vol.name}: create volume")
                self.operator.volume_create(vol)
                logger.debug(f"Volume {vol.name}: volume created")
            else:
                logger.debug(f"Volume {vol.name}: already exists")

    def _ensure_networks(self):
        for net in self.stack.networks.values():
            logger.debug(f"Network {net.name}: checking if exists")
            if not self.operator.network_exists(net.name):
                logger.debug(f"Network {net.name}: create network")
                self.operator.network_create(net)
                logger.debug(f"Network {net.name}: network created")
            else:
                logger.debug(f"Network {net.name}: already exists")
