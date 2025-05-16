from typing import Optional

import docker

from containup import containup_cli, Config
from containup.business.audit.audit_registry import AuditRegistry
from containup.business.execution_listener import ExecutionListenerStd
from containup.business.plugins.plugin_builtins import PluginBuiltins
from containup.business.plugins.plugin_registry import PluginRegistry, register
from containup.business.reports.report_generator import ReportGenerator
from containup.commands.command_down import CommandDown
from containup.commands.command_up import CommandUp
from containup.infra.docker.docker_operator import DockerOperator
from containup.infra.dryrun.dryrun_operator import DryRunOperator
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
        self._execution_listener = ExecutionListenerStd()
        register(PluginBuiltins)
        self._plugin_registry = PluginRegistry()
        self._audit_registry = AuditRegistry(self._plugin_registry)
        self._report_generator = ReportGenerator()
        self.operator = (
            DryRunOperator(self._execution_listener)
            if self.config.dry_run
            else DockerOperator(self.client)
        )
        self.user_interactions = UserInteractionsCLI()

    # Handle command line parsing and launches the commands on the stack
    def run(self):
        alerts = self._audit_registry.inspect(self.stack)
        if self.config.command == "up":
            CommandUp(self.stack, self.operator, self.user_interactions).up(
                self.config.services
            )
        elif self.config.command == "down":
            CommandDown(self.stack, self.operator).down(self.config.services)
        else:
            raise RuntimeError(f"Unrecognized command {self.config.command}")
        if self.config.dry_run:
            print(
                self._report_generator.generate_report(
                    self.stack, self.config, self._execution_listener, alerts
                ),
            )
