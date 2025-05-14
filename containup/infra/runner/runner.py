import docker
from typing import Optional
from containup import containup_cli, Config
from containup.commands.command_down import CommandDown
from containup.commands.command_up import CommandUp
from containup.infra.docker.docker_operator import DockerOperator
from containup.infra.user_interactions_cli import UserInteractionsCLI
from containup.stack.stack import Stack


class StackRunner:
    """
    Builds execution environment.

    Binds everything together for real
    - choose implementation of container
    - choose implementation of user interactions
    - give access to main run()
    """

    def __init__(self, stack: Stack, config: Optional[Config] = None):
        self.stack = stack
        self.config = config or containup_cli()
        self.client: docker.DockerClient = docker.from_env()
        self.operator = DockerOperator(self.client)
        self.user_interactions = UserInteractionsCLI()

    # Handle command line parsing and launches the commands on the stack
    def run(self):
        if self.config.command == "up":
            CommandUp(self.stack, self.operator, self.user_interactions).up(
                self.config.services
            )
        elif self.config.command == "down":
            CommandDown(self.stack, self.operator).down(self.config.services)
        else:
            raise RuntimeError(f"Unrcognized command {self.config.command}")
