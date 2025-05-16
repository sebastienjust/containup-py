import logging
from typing import List, Optional

from containup import NoneHealthcheck
from containup.commands.container_operator import (
    ContainerOperator,
    ContainerOperatorException,
)
from containup.commands.user_interactions import UserInteractions
from containup.stack.stack import Stack

logger = logging.getLogger(__name__)


class CommandUp:
    def __init__(
        self,
        stack: Stack,
        operator: ContainerOperator,
        user_interactions: UserInteractions,
    ):
        self.stack = stack
        self.operator = operator
        self.user_interactions = user_interactions

    def up(self, filter_services: Optional[List[str]] = None) -> None:
        try:
            self._ensure_volumes()
            self._ensure_networks()
            services = self.stack.get_services_sorted(filter_services)
            for service in services:
                container_name = service.container_name or service.name

                if self.operator.container_exists(container_name):
                    logger.info(f"Container {container_name} exists... removing")
                    self.operator.container_remove(container_name)
                else:
                    logger.info(f"Container {container_name} doesn't exist")

                logger.info(f"Run container {container_name} : start")
                self.operator.container_run(service)
                if service.healthcheck and not isinstance(
                    service.healthcheck, NoneHealthcheck
                ):
                    logger.info(
                        f"Run container {container_name} : wait for healthcheck"
                    )
                    self.operator.container_wait_healthy(service)
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
