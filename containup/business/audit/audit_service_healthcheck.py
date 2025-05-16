from containup.business.audit.audit_alert import (
    AuditInspector,
    AuditAlert,
    AuditAlertType,
    AuditAlertLocation,
)
from containup.stack.stack import Service
from containup.stack.stack import Stack


class AuditServiceHealthcheckInspector(AuditInspector):

    @property
    def code(self) -> str:
        return "service_healthcheck"

    def evaluate(self, stack: Stack) -> list[AuditAlert]:
        return [alert for s in stack.services for alert in healthcheck_alerts(s)]


def healthcheck_alerts(service: Service) -> list[AuditAlert]:
    """Returns alerts on healthcheck"""
    alerts: list[AuditAlert] = []

    if service.healthcheck is None:
        alerts.append(
            AuditAlert(
                AuditAlertType.INFO,
                "no healthcheck",
                AuditAlertLocation.service(service.name).healthcheck(),
            )
        )

    return alerts
