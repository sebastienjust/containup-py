import logging
import os
import sys
import time
from typing import Dict, List, Tuple, Union, cast, Optional

import docker
import requests
from docker.errors import DockerException
from docker.models.volumes import Volume

from .cli import Config
from .stack import Stack

logger = logging.getLogger(__name__)


def containup_run(stack: Stack, config: Config) -> None:
    """Run the commands on the stack"""
    StackRunner(stack=stack, config=config).run()


class StackRunner:
    def __init__(self, stack: Stack, config: Config):
        self.stack = stack
        self.config = config
        self.client: docker.DockerClient = docker.from_env()

    def _ensure_volumes(self):
        for vol in self.stack.volumes.values():
            if not any(v.name == vol for v in get_docker_volumes(self.client)):
                self.client.volumes.create(  # type: ignore
                    name=vol.name,
                    driver=vol.driver,
                    driver_opts=vol.driver_opts,
                    labels=vol.labels,
                )

    def _ensure_networks(self):
        for net in self.stack.networks.values():
            try:
                self.client.networks.get(net.name)
            except docker.errors.NotFound:  # type: ignore
                self.client.networks.create(
                    name=net.name, driver=net.driver, options=net.options
                )

    def up(self, services: Optional[List[str]] = None) -> None:
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
            typed_ports = cast(
                Dict[str, Union[int, List[int], Tuple[str, int], None]], cfg.ports
            )
            typed_volumes = self._build_volumes(cfg.volumes)
            try:
                self.client.containers.run(
                    image=cfg.image,
                    command=cfg.command,
                    stdout=True,
                    stderr=False,
                    remove=False,
                    name=container_name,
                    environment=cfg.environment,
                    ports=typed_ports,
                    volumes=typed_volumes,
                    network=cfg.network,
                    restart_policy=cfg.restart,
                    detach=True,
                )
            except DockerException as e:
                logger.error(f"Run container {container_name} : failed: {e}")
                sys.exit(1)

            if cfg.healthcheck:
                self._wait_for_health(cfg.healthcheck)

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

    def _build_volumes(
        self, volume_specs: list[str]
    ) -> Union[Dict[str, Dict[str, str]], List[str], None]:
        mounts: dict[str, dict[str, str]] = {}
        for spec in volume_specs:
            parts = spec.split(":")
            if len(parts) == 2:
                src, dst = parts
                mode = "rw"
            elif len(parts) == 3:
                src, dst, mode = parts
            else:
                continue
            src_path = os.path.abspath(src) if os.path.exists(src) else src
            mounts[src_path] = {"bind": dst, "mode": mode}
        return mounts

    def _wait_for_health(self, check: Dict[str, Union[str, int]]):
        url = cast(str, check["url"])
        interval = cast(int, check.get("interval", 15))
        timeout = cast(int, check.get("timeout", 2))
        retries = cast(int, check.get("retries", 15))
        for attempt in range(retries):
            try:
                r = requests.get(url, timeout=timeout)
                if r.status_code == 200:
                    logger.info(f"{url}")
                    return
            except Exception:
                pass
            logger.info(f"[WAIT] {url} ({attempt + 1}/{retries})")
            time.sleep(interval)
        logger.info(f"[FAIL] {url} après {retries} tentatives.")

    # Handle command line parsing and launches the commands on the stack
    def run(self):
        if self.config.command == "up":
            self.up(self.config.services)
        elif self.config.command == "down":
            self.down(self.config.services)
        elif self.config.command == "logs":
            self.logs(self.config.service)
        elif self.config.command == "export":
            print("Export -- TODO --")
        else:
            raise RuntimeError(f"Unrcognized command {self.config.command}")


def get_docker_volumes(client: docker.DockerClient) -> list[Volume]:
    return client.volumes.list()  # type: ignore[reportUnnecessaryCast]
