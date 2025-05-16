from containup.business.audit.audit_report import AuditReport
from containup.business.audit.audit_secrets import AuditSecretsInspector
from containup.business.model.audit_alert import AuditInspector, AuditAlert
from containup.stack.stack import Stack


class AuditRegistry:
    def __init__(self):
        self._inspectors: list[AuditInspector] = [AuditSecretsInspector()]

    def inspect(self, stack: Stack) -> AuditReport:
        alerts: list[AuditAlert] = [
            alert
            for inspector in self._inspectors
            for alert in inspector.evaluate(stack)
        ]
        return AuditReport(alerts)
