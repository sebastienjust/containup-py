import logging


import docker

from containup.infra.user_interactions_cli import UserInteractionsCLI

from .cli import Config
from .infra.docker.docker_operator import DockerOperator

from .stack.stack import Stack

from containup.commands.command_up import CommandUp
from containup.commands.command_down import CommandDown
from containup.commands.command_logs import CommandLogs

logger = logging.getLogger(__name__)


def containup_run(stack: Stack, config: Config) -> None:
    """Run the commands on the stack"""
    StackRunner(stack=stack, config=config).run()


class StackRunner:
    def __init__(self, stack: Stack, config: Config):
        self.stack = stack
        self.config = config
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
