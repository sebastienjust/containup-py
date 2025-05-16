from containup.business.audit.audit_secrets import AuditSecretsInspector
from containup.business.audit.audit_service_healthcheck import (
    AuditServiceHealthcheckInspector,
)
from containup.business.audit.audit_service_mounts import AuditServiceMountsInspector
from containup.business.model.audit_alert import AuditInspector
from containup.business.plugins.plugin_registry import Plugin


class PluginBuiltins(Plugin):

    @property
    def name(self) -> str:
        return "containup_builtins"

    def audit_inspectors(self) -> list[AuditInspector]:
        return [
            AuditSecretsInspector(),
            AuditServiceHealthcheckInspector(),
            AuditServiceMountsInspector(),
        ]
