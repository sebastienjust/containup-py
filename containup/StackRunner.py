import logging

import docker

from .cli import Config
from .commands import CommandDown, CommandUp
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

    # Handle command line parsing and launches the commands on the stack
    def run(self):
        if self.config.command == "up":
            CommandUp(self.stack, self.config, self.client).up(self.config.services)
        elif self.config.command == "down":
            CommandDown(self.stack, self.config, self.client).down(self.config.services)
        elif self.config.command == "logs":
            self.logs(self.config.service)
        elif self.config.command == "export":
            print("Export -- TODO --")
        else:
            raise RuntimeError(f"Unrcognized command {self.config.command}")
