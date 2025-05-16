from containup import NoneHealthcheck
from containup.business.audit.audit_alert import (
    AuditInspector,
    AuditAlert,
    AuditAlertType,
    AuditAlertLocation,
)
from containup.stack.stack import Stack


class AuditServiceDependsOnInspector(AuditInspector):

    @property
    def code(self) -> str:
        return "secrets"

    def evaluate(self, stack: Stack) -> list[AuditAlert]:
        alerts: list[AuditAlert] = []
        for service in stack.services:
            if service.depends_on:
                for dependency_name in service.depends_on:
                    dependency = next(
                        s for s in stack.services if s.name == dependency_name
                    )
                    if dependency.healthcheck is None or isinstance(
                        dependency.healthcheck, NoneHealthcheck
                    ):
                        alerts.append(
                            AuditAlert(
                                AuditAlertType.WARN,
                                f"{dependency_name} has no healthcheck",
                                AuditAlertLocation.service(service.name).depends_on(
                                    dependency_name
                                ),
                            )
                        )

        return alerts
