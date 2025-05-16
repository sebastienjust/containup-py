from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List


@dataclass
class HealthcheckOptions:
    interval: str = ""
    """
    The time to wait between checks.
    
    Time to wait between health check runs.

    Supported units: ns (nanoseconds), us or µs (microseconds), ms (milliseconds),
    s (seconds), m (minutes), h (hours). Must be 0 or at least 1 millisecond (1ms).
    0 or empty string means inherit.
    """

    timeout: str = ""
    """
    The time to wait before considering the check to have hung. 

    Supported units: ns (nanoseconds), us or µs (microseconds), ms (milliseconds),
    s (seconds), m (minutes), h (hours). Must be 0 or at least 1 millisecond (1ms).
    0 or empty string means inherit.
    """

    retries: int = 0
    """
    The number of consecutive failures needed to consider a container 
    as unhealthy.
    0 means inherit.
    """

    start_period: str = ""
    """
    Start period for the container to initialize before starting health-retries countdown. 
    It should be 0 or at least 1000000 (1 ms).
    
    Supported units: ns (nanoseconds), us or µs (microseconds), ms (milliseconds),
    s (seconds), m (minutes), h (hours). Must be 0 or at least 1 millisecond (1ms).
    0 or empty string means inherit.
    """

    start_interval: str = ""
    """
    Start period for the container to initialize before 
    starting health-retries countdown. 
    
    Supported units: ns (nanoseconds), us or µs (microseconds), ms (milliseconds),
    s (seconds), m (minutes), h (hours). Must be 0 or at least 1 millisecond (1ms).
    0 or empty string means inherit.
    """


class HealthCheck(ABC):
    type: str = "<unknown>"

    @abstractmethod
    def summary(self) -> str:
        pass


@dataclass
class InheritHealthcheck(HealthCheck):
    options: HealthcheckOptions = field(default_factory=lambda: HealthcheckOptions())
    type = "inherit"

    def summary(self) -> str:
        return "Inherited"


@dataclass
class NoneHealthcheck(HealthCheck):
    type = "none"

    def summary(self) -> str:
        return "None"


@dataclass
class CmdHealthcheck(HealthCheck):
    command: List[str]
    """
    Executes directly the command, each part part of the command being separated in the list. 

    This doesn't use a Shell. 
    Equivalent of ["CMD", args...] in docker-compose, but DON'T add CMD, just your command.
    Example:  CmdHealthcheck(["program", "-l", "INFO"])
    """
    options: HealthcheckOptions = field(default_factory=lambda: HealthcheckOptions())
    type = "cmd"

    def summary(self) -> str:
        return "(exec) " + " ".join(self.command)[:50]


@dataclass
class CmdShellHealthcheck(HealthCheck):
    command: str
    """Executes the specified command in the system's default shell"""
    options: HealthcheckOptions = field(default_factory=lambda: HealthcheckOptions())
    type = "cmd_shell"

    def summary(self) -> str:
        return "(shell) " + self.command[:50]
