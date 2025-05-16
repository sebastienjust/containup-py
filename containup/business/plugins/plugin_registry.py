from abc import ABC, abstractmethod

from containup.business.audit.audit_alert import AuditInspector


class Plugin(ABC):
    """Base class for plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    def audit_inspectors(self) -> list[AuditInspector]:
        return []


# Registry to store run-time plugins
_registry: list[type[Plugin]] = []


def _get_all_plugins() -> list[Plugin]:
    """Returns list of all plugins instanciated."""
    return [cls() for cls in _registry]


def register(inpector_cls: type[Plugin]):
    """
    Allows registering plugin.

    Bring your own plugin
    """
    _registry.append(inpector_cls)


class PluginRegistry:
    """Maintains and query the list of audit inspectors."""

    _audit_inspectors: list[AuditInspector] = []

    def __init__(self):
        self._plugins = _get_all_plugins()
        self._audit_inspectors = [
            it for plugin in self._plugins for it in plugin.audit_inspectors()
        ]
        pass

    def get_all_inspectors(self) -> list[AuditInspector]:
        return self._audit_inspectors
