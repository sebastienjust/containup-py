import logging
from typing import List, Optional

from containup import Network, NoneHealthcheck, Volume
from containup.business.commands.container_operator import (
    ContainerOperator,
    ContainerOperatorException,
)
from containup.business.commands.user_interactions import UserInteractions
from containup.business.execution_listener import (
    ExecutionEvtContainerRemoved,
    ExecutionEvtContainerRun,
    ExecutionEvtImagePull,
    ExecutionEvtNetworkCreated,
    ExecutionEvtVolumeCreated,
    ExecutionListener,
)
from containup.business.live_state.stack_state import StackState
from containup.stack.service import Service
from containup.stack.service_healthcheck import HealthcheckOptions
from containup.stack.stack import Stack
from containup.utils.duration_to_nano import duration_to_seconds

logger = logging.getLogger(__name__)


class CommandUp:
    """
    Puts the stack up

    Args:
        dry_run (bool): we don't do any changes to the system
        live_check (bool): in dry run, we try to check if real things exists
    """

    def __init__(
        self,
        stack: Stack,
        operator: ContainerOperator,
        system_interactions: UserInteractions,
        auditor: ExecutionListener,
        dry_run: bool,
        live_check: bool,
        stack_state: StackState,
    ):
        self.stack = stack
        self.operator = operator
        self._system_interactions = system_interactions
        self._system_read = live_check if dry_run else True
        self._system_write = not dry_run
        self._auditor = auditor
        self._stack_state = stack_state

    def up(self, filter_services: Optional[List[str]] = None) -> None:
        try:

            self._ensure_volumes()
            self._ensure_networks()

            services = self.stack.get_services_sorted(filter_services)
            self._ensure_images(services)

            for service in services:
                container_name = service.container_name_safe()
                state = self._stack_state.get_container_state(container_name)
                if state == "exists":
                    logger.info(f"Container {container_name} exists... removing")
                    if self._system_write:
                        self.operator.container_remove(container_name)
                    self._auditor.record(ExecutionEvtContainerRemoved(container_name))
                else:
                    logger.info(f"Container {container_name} doesn't exist")

            for service in services:
                container_name = service.container_name or service.name

                if self._system_write:
                    logger.info(f"Run container {container_name} : start")
                    self.operator.container_run(self.stack.name, service)

                self._auditor.record(ExecutionEvtContainerRun(container_name, service))

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
        for vol in self.stack.volumes:
            self._ensure_volume(vol)

    def _ensure_volume(self, vol: Volume):
        logger.debug(f"Volume {vol.name}: checking if exists")
        state = self._stack_state.get_volume_state(vol.name)
        if state != "exists":
            logger.debug(f"Volume {vol.name}: create volume")
            self._auditor.record(ExecutionEvtVolumeCreated(vol.name, vol))
            if self._system_write:
                self.operator.volume_create(self.stack.name, vol)
            logger.debug(f"Volume {vol.name}: volume created")
        else:
            logger.debug(f"Volume {vol.name}: already exists")

    def _ensure_networks(self):
        for net in self.stack.networks:
            self._ensure_network(net)

    def _ensure_network(self, net: Network):
        logger.debug(f"Network {net.name}: checking if exists")
        state = self._stack_state.get_network_state(net.name)
        if state != "exists":
            logger.debug(f"Network {net.name}: create network")
            self._auditor.record(ExecutionEvtNetworkCreated(net.name, net))
            if self._system_write:
                self.operator.network_create(self.stack.name, net)
            logger.debug(f"Network {net.name}: network created")
        else:
            logger.debug(f"Network {net.name}: already exists")

    def _ensure_images(self, containers: list[Service]):
        for container in containers:
            self._ensure_image(container)

    def _ensure_image(self, container: Service):
        image = container.image
        state = self._stack_state.get_image_state(container.image)
        if state != "exists":
            logger.debug(f"Image {image}: pulling")
            self._auditor.record(ExecutionEvtImagePull(image))
            if self._system_write:
                self.operator.image_pull(image)

    def _container_wait_healthy(self, service: Service) -> None:

        # We don't want to do that in dry-run mode
        if not self._system_write:
            return

        # If no healthcheck defined, do nothing
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

        while self._system_interactions.time() < deadline and attempt < max_attempts:
            state = self.operator.container_health_status(container_name)
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
