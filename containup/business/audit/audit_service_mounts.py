from pathlib import PurePosixPath

from containup.business.audit.audit_alert import (
    AuditInspector,
    AuditAlert,
    AuditAlertType,
    AuditAlertLocation,
)
from containup.stack.service_mounts import ServiceMount, BindMount
from containup.stack.stack import Stack, Service


class AuditServiceMountsInspector(AuditInspector):

    @property
    def code(self) -> str:
        return "service_mounts"

    def evaluate(self, stack: Stack) -> list[AuditAlert]:
        return [
            alert
            for s in stack.services
            for mount in s.mounts_all()
            for alert in mount_alert(s, mount, s.mounts_all())
        ]


def mount_alert(
    service: Service, mount: ServiceMount, all_mounts: list[ServiceMount]
) -> list[AuditAlert]:
    """Returns alerts on mount"""

    alerts: list[AuditAlert] = []
    if isinstance(mount, BindMount):
        for prefix in ["etc", "var", "home", "root"]:
            if mount.source.startswith("/" + prefix):
                alerts.append(
                    AuditAlert(
                        AuditAlertType.CRITICAL,
                        "sensitive host path",
                        AuditAlertLocation.service(service.name).mount(mount.id),
                    )
                )
        if mount.read_only is None:
            alerts.append(
                AuditAlert(
                    AuditAlertType.WARN,
                    "default to read-write, make it explicit",
                    AuditAlertLocation.service(service.name).mount(mount.id),
                )
            )

    conflicts = find_mount_conflicts(mount, all_mounts)
    for conflict in conflicts:
        alerts.append(
            AuditAlert(
                AuditAlertType.CRITICAL,
                "conflicting mount path with " + conflict.target,
                AuditAlertLocation.service(service.name).mount(mount.id),
            )
        )

    if not mount.target.startswith("/"):
        alerts.append(
            AuditAlert(
                AuditAlertType.CRITICAL,
                "relative target path",
                AuditAlertLocation.service(service.name).mount(mount.id),
            )
        )

    if isinstance(mount, BindMount) and not mount.source.startswith("/"):
        alerts.append(
            AuditAlert(
                AuditAlertType.CRITICAL,
                "relative source path",
                AuditAlertLocation.service(service.name).mount(mount.id),
            )
        )

    return alerts


def is_relative_to(child: PurePosixPath, parent: PurePosixPath) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def find_mount_conflicts(
    mount: ServiceMount, all_mounts: list[ServiceMount]
) -> list[ServiceMount]:
    target_path = PurePosixPath(mount.target)
    conflicts: list[ServiceMount] = []

    for other in all_mounts:
        if other.id == mount.id:
            continue
        other_path = PurePosixPath(other.target)
        if target_path == other_path:
            conflicts.append(other)
        elif is_relative_to(target_path, other_path) or is_relative_to(
            other_path, target_path
        ):
            conflicts.append(other)

    return conflicts
