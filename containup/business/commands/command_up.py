import logging
from typing import List, Optional

from containup import NoneHealthcheck
from containup.business.commands.container_operator import (
    ContainerOperator,
    ContainerOperatorException,
)
from containup.business.commands.user_interactions import UserInteractions
from containup.stack.service import Service
from containup.stack.service_healthcheck import HealthcheckOptions
from containup.stack.stack import Stack
from containup.utils.duration_to_nano import duration_to_seconds

logger = logging.getLogger(__name__)


class CommandUp:
    def __init__(
        self,
        stack: Stack,
        operator: ContainerOperator,
        system_interactions: UserInteractions,
    ):
        self.stack = stack
        self.operator = operator
        self._system_interactions = system_interactions

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
                    self._container_wait_healthy(service)
                logger.info(f"Run container {container_name} : start done")

        except ContainerOperatorException as e:
            logger.error(f"Command up failed: {e}")
            self._system_interactions.exit_with_error(1)

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

    def _container_wait_healthy(self, service: Service) -> None:
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
            self._system_interactions.time()
            + timeout * retries * interval
            + start_period
            + start_interval
        )
        attempt: int = 0

        container_name = service.container_name_safe()

        logger.info(
            f"Wait container {container_name} plan. Interval: {interval} timeout: {timeout} retries: {retries}"
        )

        state = self.operator.container_health_status(container_name)
        while self._system_interactions.time() < deadline and attempt < max_attempts:
            health = state.health
            status = state.status
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

            self._system_interactions.sleep(interval)

        raise ContainerOperatorException(
            f"Container {container_name} did not become healthy in time."
        )
