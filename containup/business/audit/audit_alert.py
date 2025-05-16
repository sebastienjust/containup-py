from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from containup.stack.stack import Stack


class AuditAlertType(str, Enum):
    INFO = "info"
    WARN = "warn"
    CRITICAL = "critical"


class AuditLocations(str, Enum):
    SERVICE = "service"
    ENVIRONMENT = "environment"
    HEALTHCHECK = "heathcheck"
    MOUNT = "mount"
    IMAGE = "image"


@dataclass
class AuditAlertLocation:
    location: list[str]

    @staticmethod
    def service(service_name: str):
        return AuditAlertLocation([AuditLocations.SERVICE, service_name])

    def environment(self, key: str):
        return AuditAlertLocation(self.location + [AuditLocations.ENVIRONMENT, key])

    def healthcheck(self):
        return AuditAlertLocation(self.location + [AuditLocations.HEALTHCHECK])

    def mount(self, mount_id: str):
        return AuditAlertLocation(self.location + [AuditLocations.MOUNT, mount_id])

    def image(self):
        return AuditAlertLocation(self.location + [AuditLocations.IMAGE])


@dataclass
class AuditAlert:
    severity: AuditAlertType
    message: str
    location: AuditAlertLocation


class AuditInspector(ABC):

    @property
    @abstractmethod
    def code(self) -> str:
        pass

    @abstractmethod
    def evaluate(self, stack: Stack) -> list[AuditAlert]:
        pass
