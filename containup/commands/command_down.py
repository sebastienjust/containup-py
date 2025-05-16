import logging
from typing import Optional

from containup.commands.container_operator import (
    ContainerOperator,
    ContainerOperatorException,
)
from containup.stack.stack import (
    Stack,
)

logger = logging.getLogger(__name__)


class CommandDown:

    def __init__(self, stack: Stack, operator: ContainerOperator):
        self.stack = stack
        self.operator = operator

    def down(self, filter_services: Optional[list[str]] = None) -> None:
        services = self.stack.get_services_sorted(filter_services)[::-1]
        for service in services:
            container_name = service.container_name or service.name
            try:
                if self.operator.container_exists(container_name):
                    logger.info(
                        f"Remove container {container_name}: container exists, removing."
                    )
                    self.operator.container_remove(container_name)
                    logger.info(
                        f"Remove container {container_name}: container removed."
                    )
                else:
                    logger.info(
                        f"Remove container {container_name}: container doesn't exist."
                    )
            except ContainerOperatorException:  # type: ignore
                logger.info(f"Remove container {service.name}: not found.")
                continue
