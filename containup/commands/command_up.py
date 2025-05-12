import logging
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

import docker
from docker.errors import DockerException
from docker.models.volumes import Volume
from docker.types import Mount

from containup.stack.service_healthcheck import (
    CmdHealthcheck,
    CmdShellHealthcheck,
    HealthCheck,
    InheritHealthcheck,
    NoneHealthcheck,
)
from containup.stack.service_mounts import (
    BindMount,
    ServiceMounts,
    TmpfsMount,
    VolumeMount,
)
from containup.stack.service_ports import ServicePortMapping
from containup.stack.stack import (
    Stack,
)
from containup.utils.absolute_paths import to_absolute_path
from containup.utils.duration_to_nano import duration_to_nano

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
            typed_ports = self.to_docker_ports(cfg.ports)
            mounts = self._build_mounts(cfg.mounts_all())
            try:
                self.client.containers.run(
                    image=cfg.image,
                    command=cfg.command,
                    stdout=True,
                    stderr=False,
                    remove=False,
                    name=container_name,
                    environment=cfg.environment,
                    ports=typed_ports,  # type: ignore
                    mounts=mounts,
                    network=cfg.network,
                    restart_policy=cfg.restart,
                    detach=True,
                    healthcheck=(
                        None
                        if cfg.healthcheck is None
                        else healthcheck_to_docker_spec(cfg.healthcheck)
                    ),
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

    def to_docker_port(
        self, mapping: ServicePortMapping
    ) -> Tuple[str, Union[int, Tuple[str, int]]]:
        key = f"{mapping.container_port}/{mapping.protocol}"
        value: Union[int, Tuple[str, int]]
        if mapping.host_ip is None:
            value = mapping.host_port or mapping.container_port
        else:
            value = (mapping.host_ip, mapping.host_port or mapping.container_port)
        return key, value

    def to_docker_ports(
        self, mappings: List[ServicePortMapping]
    ) -> Dict[str, List[Union[int, Tuple[str, int]]]]:
        result: Dict[str, List[Union[int, Tuple[str, int]]]] = {}

        for m in mappings:
            key, value = self.to_docker_port(m)
            if key not in result:
                result[key] = [value]
            else:
                result[key].append(value)

        return result

    def _build_mounts(self, volume_specs: ServiceMounts) -> List[Mount]:
        result: list[Mount] = []
        for m in volume_specs:
            if isinstance(m, BindMount):
                result.append(
                    Mount(
                        type="bind",
                        source=to_absolute_path(m.source),
                        target=m.target,
                        read_only=m.read_only,
                        consistency=m.consistency,
                        propagation=m.propagation,
                    )
                )
            elif isinstance(m, VolumeMount):
                result.append(
                    Mount(
                        type="volume",
                        source=m.source,
                        target=m.target,
                        read_only=m.read_only,
                        consistency=m.consistency,
                        no_copy=m.no_copy,
                        labels=m.labels,
                        driver_config=m.driver_config,
                    )
                )
            elif isinstance(m, TmpfsMount):  # type: ignore
                result.append(
                    Mount(
                        source=None,
                        type="tmpfs",
                        target=m.target,
                        read_only=m.read_only,
                        consistency=m.consistency,
                        tmpfs_size=m.tmpfs_size,
                        tmpfs_mode=m.tmpfs_mode,
                    )
                )
            else:
                raise TypeError(f"Unsupported mount type: {type(m)}")
        return result


def get_docker_volumes(client: docker.DockerClient) -> list[Volume]:
    return client.volumes.list()  # type: ignore[reportUnnecessaryCast]


def healthcheck_to_docker_spec(item: HealthCheck) -> Dict[str, Any]:

    interval: int = duration_to_nano(item.options.interval)
    timeout: int = duration_to_nano(item.options.timeout)
    retries: int = item.options.retries
    start_period: int = duration_to_nano(item.options.start_period)

    if isinstance(item, InheritHealthcheck):
        return {
            "test": [],
            "interval": interval,
            "timeout": timeout,
            "retries": retries,
            "start_period": start_period,
        }
    elif isinstance(item, NoneHealthcheck):
        return {
            "test": ["NONE"],
            "interval": interval,
            "timeout": timeout,
            "retries": retries,
            "start_period": start_period,
        }
    elif isinstance(item, CmdHealthcheck):
        return {
            "test": ["CMD"] + item.command,
            "interval": interval,
            "timeout": timeout,
            "retries": retries,
            "start_period": start_period,
        }

    elif isinstance(item, CmdShellHealthcheck):  # type: ignore
        return {
            "test": ["CMD-SHELL", item.command],
            "interval": interval,
            "timeout": timeout,
            "retries": retries,
            "start_period": start_period,
        }

    raise RuntimeError(f"Unknown type of healthcheck {item}")
