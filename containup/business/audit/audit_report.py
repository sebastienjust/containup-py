from containup.business.model.audit_alert import AuditAlert, AuditAlertLocation


class AuditReport:
    def __init__(self, alerts: list[AuditAlert]):
        self._alerts = alerts

    def query(self, location: AuditAlertLocation) -> list[AuditAlert]:
        return [alert for alert in self._alerts if alert.location == location]
