from containup.business.audit.audit_alert import AuditAlert, AuditAlertLocation


class AuditResult:
    """
    Contains the result of stack auditing.

    Implemented as a wrapper around a list of :class:`AuditAlert` with helper methods to
    filter and find relevant alerts.
    """

    def __init__(self, alerts: list[AuditAlert]):
        self._alerts = alerts

    def query(self, location: AuditAlertLocation) -> list[AuditAlert]:
        return [alert for alert in self._alerts if alert.location == location]
