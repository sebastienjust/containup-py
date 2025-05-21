from typing import Optional

import docker

from containup import containup_cli, Config
from containup.business.audit.audit_registry import AuditRegistry
from containup.business.commands.command_down import CommandDown
from containup.business.commands.command_up import CommandUp
from containup.business.execution_listener import ExecutionListenerStd
from containup.business.live_state.stack_state import StackState
from containup.business.live_state.stack_state_resolver import StackStateResolver
from containup.business.plugins.plugin_builtins import PluginBuiltins
from containup.business.plugins.plugin_registry import PluginRegistry, register
from containup.business.reports.report_generator import ReportGenerator
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

    # Handle command line parsing and launches the commands on the stack
    def run(self):

        # Audit the stack (no live access here, just static checks)
        alerts = self._audit_registry.inspect(self.stack)

        # tells if we run for real (true) or of we are not connected to any system (false)
        live_operations = (
            (self.config.command == "check" and self.config.live_check)
            or (self.config.command == "up" and not self.config.dry_run)
            or (
                self.config.command == "up"
                and self.config.dry_run
                and self.config.live_check
            )
            or (self.config.command == "down" and not self.config.dry_run)
            or (
                self.config.command == "down"
                and self.config.dry_run
                and self.config.live_check
            )
        )

        # if we shall not be connected to live systems, use the DryRunOperator to be sure
        # that nothing goes to Doccker
        operator = (
            DockerOperator(self.client, self.system_interactions)
            if live_operations
            else DryRunOperator(self._execution_listener)
        )

        # Take the stack and check its state. If we are not "live" just return an empty State
        # with everything marked as "unknown", otherwise, check the live status of the system.
        stack_state = (
            StackState()
            if not live_operations
            else StackStateResolver(operator).resolve(self.stack)
        )

        # Report is displayed if we launch "check" or any command with --dry-run
        generate_report = self.config.command == "check" or self.config.dry_run

        if self.config.command == "up":
            CommandUp(
                stack=self.stack,
                operator=operator,
                system_interactions=self.system_interactions,
                auditor=self._execution_listener,
                dry_run=self.config.dry_run,
                live_check=self.config.live_check,
                stack_state=stack_state,
            ).up(self.config.services)
        elif self.config.command == "down":
            CommandDown(
                stack=self.stack,
                operator=operator,
                auditor=self._execution_listener,
                dry_run=self.config.dry_run,
                live_check=self.config.live_check,
                stack_state=stack_state,
            ).down(self.config.services)
        elif self.config.command == "check":
            pass
        else:
            raise RuntimeError(f"Unimplemented command [{self.config.command}]")

        if generate_report:
            print(
                self._report_generator.generate_report(
                    stack=self.stack,
                    config=self.config,
                    listener=self._execution_listener,
                    alerts=alerts,
                    stack_state=stack_state,
                    live_operations=live_operations,
                ),
            )
