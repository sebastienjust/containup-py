from typing import Union

from containup.business.audit.audit_alert import (
    AuditInspector,
    AuditAlert,
    AuditAlertType,
    AuditAlertLocation,
)
from containup.stack.stack import Stack
from containup.utils.secret_value import SecretValue


class AuditSecretsInspector(AuditInspector):

    @property
    def code(self) -> str:
        return "secrets"

    def evaluate(self, stack: Stack) -> list[AuditAlert]:
        return [
            alert
            for s in stack.services
            for k, v in s.environment.items()
            for alert in secrets_alerts(s.name, k, v)
        ]


def secrets_alerts(
    service_id: str, k: str, v: Union[str, SecretValue]
) -> list[AuditAlert]:
    alerts: list[AuditAlert] = []

    secret_like_keys = {"password", "token", "secret", "key", "pwd", "pass"}
    lowered = k.lower()
    if any(hint in lowered for hint in secret_like_keys):
        if not isinstance(v, SecretValue):
            alerts.append(
                AuditAlert(
                    AuditAlertType.CRITICAL,
                    "looks like a secret but is passed as plaintext — use containup.secret() to redact it safely",
                    AuditAlertLocation.service(service_id).environment(k),
                ),
            )

    return alerts
