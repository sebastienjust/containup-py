from dataclasses import dataclass


@dataclass
class ContainerHealthStatus:
    status: str
    """Can be: unknown, exited"""
    health: str
    """Can be: unknown, healthy, unhealthy"""
