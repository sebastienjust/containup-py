import docker
import os
import time
import requests
import logging
import sys
import argparse

from typing import Optional, TypedDict, NotRequired, Literal, cast
from dataclasses import dataclass, field
from docker.models.volumes import Volume
from docker.errors import DockerException

# TODO get that from elswhere
VERSION = "0.1.0"

# Initialize logger for this lib. Don't force the logger
logger = logging.getLogger(__name__)

class _RestartPolicy(TypedDict):
    MaximumRetryCount: NotRequired[int]
    Name: NotRequired[Literal["always", "on-failure"]]


@dataclass
class ServiceCfg:
    name: str
    image: str
    container_name: str
    ports: dict[str, int] = field(default_factory=dict)
    environment: dict[str, str] = field(default_factory=dict)
    volumes: list[str] = field(default_factory=list)
    network: Optional[str] = None
    command: list[str] = field(default_factory=list)
    restart: Optional[_RestartPolicy] = None
    healthcheck: dict[str, int | str] = field(default_factory=dict)


class Stack:
    def __init__(self, name: str, args: argparse.Namespace):
        self.name = name
        self.client: docker.DockerClient = docker.from_env()
        self.volumes: dict[str, str] = {}
        self.networks: dict[str, str] = {}
        self.services: dict[str, ServiceCfg] = {}
        self.args: argparse.Namespace = args

    def volume(self, name: str):
        self.volumes[name] = name

    def network(self, name: str):
        self.networks[name] = name

    def service(self, cfg: ServiceCfg) -> None:
        self.services[cfg.name] = cfg

    def _ensure_volumes(self):
        for vol in self.volumes.values():
            if not any(v.name == vol for v in get_docker_volumes(self.client)):
                self.client.volumes.create(name=vol)  # type: ignore

    def _ensure_networks(self):
        for net in self.networks.values():
            try:
                self.client.networks.get(net)
            except docker.errors.NotFound:  # type: ignore
                self.client.networks.create(name=net)

    def up(self, services: list[str] | None = None) -> None:
        self._ensure_volumes()
        self._ensure_networks()
        targets = (
            self.services.values()
            if services is None
            else (self.services[k] for k in services)
        )
        for cfg in targets:
            container_name = cfg.container_name
            try:
                logger.info(f"Remove container if exists {container_name}")
                self.client.containers.get(container_name).remove(force=True)
            except docker.errors.NotFound:  # type: ignore
                pass

            logger.info(f"Run container {container_name} : start")
            typed_ports = cast(
                dict[str, int | list[int] | tuple[str, int] | None], cfg.ports
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
            self.services
            if services is None
            else {k: self.services[k] for k in services}
        )
        for name, cfg in targets.items():
            container_name = cfg.container_name
            try:
                logger.info(f"Remove container {name} : start")
                self.client.containers.get(container_name).remove(force=True)
                logger.info(f"Remove container {name} : done")
            except docker.errors.NotFound:  # type: ignore
                logger.info(f"Remove container {name} : not found")
                continue

    def logs(self, service: str) -> None:
        cfg = self.services[service]
        container_name = cfg.container_name
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
    ) -> dict[str, dict[str, str]] | list[str] | None:
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

    def _wait_for_health(self, check: dict[str, str | int]):
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
        logger.info(f"Stating with {self.args} and extra args {self.args.extra_args}")
        if self.args.command == 'up':
            self.up([self.args.service] if self.args.service else None)
        elif self.args.command == "down":
            self.down([self.args.service])
        elif self.args.command == "logs":
            self.logs(self.args.service)
        elif self.args.command == "export":
            print("Export -- TODO --")
        else:
            sys.exit(1)


def get_docker_volumes(client: docker.DockerClient) -> list[Volume]:
    return client.volumes.list()  # type: ignore[reportUnnecessaryCast]

def containup_cli() -> argparse.Namespace: 
    parser = argparse.ArgumentParser(prog=sys.argv[0])
    parser.add_argument('--version', action = 'version', version=f'%(prog)s using containup {VERSION}')
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    p = subparsers.add_parser("up")
    p.add_argument('service', nargs='?', help=f'Launches this service only')
    p.add_argument('extra_args', nargs=argparse.REMAINDER, help="Your own arguments")

    p = subparsers.add_parser("down")
    p.add_argument('service', nargs='?', help=f'Stop this service only')
    p.add_argument('extra_args', nargs=argparse.REMAINDER, help="Your own arguments")

    logs_parser = subparsers.add_parser('logs')
    logs_parser.add_argument('service', help='Get logs from service')
    p.add_argument('extra_args', nargs=argparse.REMAINDER, help="Your own arguments")

    subparsers.add_parser('export')
    p.add_argument('extra_args', nargs=argparse.REMAINDER, help="Your own arguments")
    
    args = parser.parse_args()

    if (args.command not in ["up", "down", "logs", "export"]):
        parser.print_help()
        sys.exit(1)

    return args 

