from typing import List, Union
from dataclasses import dataclass


@dataclass
class HealthcheckOptions:
    interval: str
    """
    The time to wait between checks.
    
    Time to wait between health check runs.

    Supported units: ns (nanoseconds), us or µs (microseconds), ms (milliseconds),
    s (seconds), m (minutes), h (hours). Must be 0 or at least 1 millisecond (1ms).
    """

    timeout: str
    """
    The time to wait before considering the check to have hung. 

    Supported units: ns (nanoseconds), us or µs (microseconds), ms (milliseconds),
    s (seconds), m (minutes), h (hours). Must be 0 or at least 1 millisecond (1ms).
    """

    retries: int
    """
    The number of consecutive failures needed to consider a container 
    as unhealthy.
    """

    start_period: str
    """
    Start period for the container to initialize before 
    starting health-retries countdown. 
    
    Supported units: ns (nanoseconds), us or µs (microseconds), ms (milliseconds),
    s (seconds), m (minutes), h (hours). Must be 0 or at least 1 millisecond (1ms).
    """


@dataclass
class InheritHealthcheck:
    options: HealthcheckOptions


@dataclass
class NoneHealthcheck:
    options: HealthcheckOptions


@dataclass
class CmdHealthcheck:
    command: List[str]
    options: HealthcheckOptions


@dataclass
class CmdShellHealthcheck:
    command: str
    options: HealthcheckOptions


HealthCheck = Union[
    CmdShellHealthcheck, CmdHealthcheck, NoneHealthcheck, InheritHealthcheck
]
