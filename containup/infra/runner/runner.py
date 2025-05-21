from typing import Optional

import docker

from containup import containup_cli, Config
from containup.business.audit.audit_registry import AuditRegistry
from containup.business.execution_listener import ExecutionListenerStd
from containup.business.live_state.stack_state import StackState
from containup.business.live_state.stack_state_resolver import StackStateResolver
from containup.business.plugins.plugin_builtins import PluginBuiltins
from containup.business.plugins.plugin_registry import PluginRegistry, register
from containup.business.reports.report_generator import ReportGenerator
from containup.business.commands.command_down import CommandDown
from containup.business.commands.command_up import CommandUp
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
        self.system_interactions = UserInteractionsCLI()
        self.operator = (
            DryRunOperator(self._execution_listener)
            if self.config.dry_run and not self.config.live_check
            else DockerOperator(self.client, self.system_interactions)
        )

    # Handle command line parsing and launches the commands on the stack
    def run(self):
        alerts = self._audit_registry.inspect(self.stack)
        stack_state = (
            StackState()
            if (self.config.dry_run and not self.config.live_check)
            else StackStateResolver(self.operator).resolve(self.stack)
        )
        if self.config.command == "up":
            CommandUp(
                stack=self.stack,
                operator=self.operator,
                system_interactions=self.system_interactions,
                auditor=self._execution_listener,
                dry_run=self.config.dry_run,
                live_check=self.config.live_check,
                stack_state=stack_state,
            ).up(self.config.services)
        elif self.config.command == "down":

            CommandDown(
                stack=self.stack,
                operator=self.operator,
                auditor=self._execution_listener,
                dry_run=self.config.dry_run,
                live_check=self.config.live_check,
                stack_state=stack_state,
            ).down(self.config.services)
        else:
            raise RuntimeError(f"Unrecognized command {self.config.command}")
        if self.config.dry_run:
            print(
                self._report_generator.generate_report(
                    stack=self.stack,
                    config=self.config,
                    listener=self._execution_listener,
                    alerts=alerts,
                    stack_state=stack_state,
                ),
            )
