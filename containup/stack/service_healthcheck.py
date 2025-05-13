from dataclasses import dataclass, field
from typing import List, Union


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


@dataclass
class InheritHealthcheck:
    options: HealthcheckOptions = field(default_factory=lambda: HealthcheckOptions())


@dataclass
class NoneHealthcheck:
    pass


@dataclass
class CmdHealthcheck:
    command: List[str]
    options: HealthcheckOptions = field(default_factory=lambda: HealthcheckOptions())


@dataclass
class CmdShellHealthcheck:
    command: str
    options: HealthcheckOptions = field(default_factory=lambda: HealthcheckOptions())


HealthCheck = Union[
    CmdShellHealthcheck, CmdHealthcheck, NoneHealthcheck, InheritHealthcheck
]
