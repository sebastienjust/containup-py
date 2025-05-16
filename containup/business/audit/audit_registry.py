from containup.business.audit.audit_report import AuditResult
from containup.business.audit.audit_alert import AuditAlert
from containup.business.plugins.plugin_registry import PluginRegistry
from containup.stack.stack import Stack


class AuditRegistry:
    """Maintains and query the list of audit inspectors."""

    def __init__(self, plugins: PluginRegistry):
        self._plugins = plugins

    def inspect(self, stack: Stack) -> AuditResult:
        """Runs the stack over all audit inspectors and generates an audit report."""
        alerts: list[AuditAlert] = [
            alert
            for inspector in self._plugins.get_all_inspectors()
            for alert in inspector.evaluate(stack)
        ]
        return AuditResult(alerts)
