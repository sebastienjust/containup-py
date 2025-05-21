import logging
from typing import Optional

from containup.business.commands.container_operator import (
    ContainerOperator,
    ContainerOperatorException,
)
from containup.business.execution_listener import (
    ExecutionEvtContainerExistsCheck,
    ExecutionEvtContainerRemoved,
    ExecutionListener,
)
from containup.stack.stack import (
    Stack,
)

logger = logging.getLogger(__name__)


class CommandDown:

    def __init__(
        self,
        stack: Stack,
        operator: ContainerOperator,
        auditor: ExecutionListener,
        dry_run: bool,
        live_check: bool,
    ):
        self.stack = stack
        self.operator = operator
        self._system_read = live_check if dry_run else True
        self._system_write = not dry_run
        self._auditor = auditor

    def down(self, filter_services: Optional[list[str]] = None) -> None:
        services = self.stack.get_services_sorted(filter_services)[::-1]
        for service in services:
            container_name = service.container_name or service.name
            try:
                container_exists: Optional[bool] = None
                if self._system_read:
                    logger.info(f"Remove container {container_name}: check if exists.")
                    container_exists = self.operator.container_exists(container_name)
                self._auditor.record(
                    ExecutionEvtContainerExistsCheck(container_name, container_exists)
                )

                if container_exists == True or container_exists is None:
                    if self._system_write:
                        logger.info(
                            f"Remove container {container_name}: container exists, removing."
                        )
                        self.operator.container_remove(container_name)
                        logger.info(
                            f"Remove container {container_name}: container removed."
                        )
                    self._auditor.record(ExecutionEvtContainerRemoved(container_name))
                else:
                    logger.info(
                        f"Remove container {container_name}: container doesn't exist."
                    )
            except ContainerOperatorException:  # type: ignore
                logger.info(f"Remove container {service.name}: not found.")
                continue
