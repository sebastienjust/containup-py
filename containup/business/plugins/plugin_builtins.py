from containup.business.audit.audit_alert import AuditInspector
from containup.business.audit.audit_container_image import AuditServiceImageInspector
from containup.business.audit.audit_depends_on import AuditServiceDependsOnInspector
from containup.business.audit.audit_secrets import AuditSecretsInspector
from containup.business.audit.audit_service_healthcheck import (
    AuditServiceHealthcheckInspector,
)
from containup.business.audit.audit_service_mounts import AuditServiceMountsInspector
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
            AuditServiceImageInspector(),
            AuditServiceDependsOnInspector(),
        ]
