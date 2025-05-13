import logging
from typing import Optional

import docker

from containup.commands.command_down import CommandDown
from containup.commands.command_logs import CommandLogs
from containup.commands.command_up import CommandUp
from containup.infra.user_interactions_cli import UserInteractionsCLI
from . import containup_cli
from .cli import Config
from .infra.docker.docker_operator import DockerOperator
from .stack.stack import Stack

logger = logging.getLogger(__name__)


def containup_run(stack: Stack, config: Optional[Config] = None) -> None:
    """
    Runs commands given from the config over the stack.

    Args:
        stack: stack to run
        config: if None (most ot your use cases) command line arguments will be taken from the CLI
    """
    StackRunner(stack=stack, config=config).run()


class StackRunner:
    def __init__(self, stack: Stack, config: Optional[Config] = None):
        self.stack = stack
        self.config = config or containup_cli()
        self.client: docker.DockerClient = docker.from_env()
        self.operator = DockerOperator(self.client)
        self.user_interactions = UserInteractionsCLI()

    # Handle command line parsing and launches the commands on the stack
    def run(self):
        if self.config.command == "up":
            CommandUp(
                self.stack, self.client, self.operator, self.user_interactions
            ).up(self.config.services)
        elif self.config.command == "down":
            CommandDown(self.stack, self.client).down(self.config.services)
        elif self.config.command == "logs":
            CommandLogs(self.stack, self.client).logs(self.config.service)
        elif self.config.command == "export":
            print("Export -- TODO --")
        else:
            raise RuntimeError(f"Unrcognized command {self.config.command}")
