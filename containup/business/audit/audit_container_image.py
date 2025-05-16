from containup import Stack
from containup.business.audit.audit_alert import (
    AuditAlert,
    AuditAlertType,
    AuditAlertLocation,
    AuditInspector,
)


class AuditServiceImageInspector(AuditInspector):

    @property
    def code(self) -> str:
        return "secrets"

    def evaluate(self, stack: Stack) -> list[AuditAlert]:
        return [
            alert for s in stack.services for alert in image_tag_alert(s.name, s.image)
        ]


def image_tag_alert(service_name: str, image: str) -> list[AuditAlert]:
    """Returns a warning if the image uses a risky tag (latest, implicit, unstable)."""

    risky_tags = {"latest", "dev", "nightly", "snapshot", "beta", "alpha", "rc"}

    location = AuditAlertLocation.service(service_name).image()

    if ":" not in image:
        return [
            AuditAlert(
                AuditAlertType.CRITICAL,
                "image has no explicit tag (defaults to :latest)",
                location,
            )
        ]

    _, tag = image.rsplit(":", 1)

    if tag == "latest":
        return [AuditAlert(AuditAlertType.CRITICAL, "image uses tag :latest", location)]

    if tag in risky_tags:
        return [
            AuditAlert(AuditAlertType.WARN, f"image uses unstable tag :{tag}", location)
        ]

    if not any(char.isdigit() for char in tag):
        return [
            AuditAlert(AuditAlertType.CRITICAL, f"image tag is vague :{tag}", location)
        ]

    return []
