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


@dataclass
class AuditAlertLocation:
    location: list[str]


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
