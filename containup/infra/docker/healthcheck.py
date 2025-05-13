from typing import Any, Dict, Union

from containup import (
    HealthCheck,
    CmdHealthcheck,
    NoneHealthcheck,
    InheritHealthcheck,
    CmdShellHealthcheck,
    HealthcheckOptions,
)
from containup.utils.duration_to_nano import duration_to_nano


def healthcheck_to_docker_spec_unsafe(
    item: Union[HealthCheck, None],
) -> Union[Dict[str, Any], None]:
    """
    Unsafe version of healthcheck_to_docker_spec to allow returning None
    if there are None healthcheck
    """
    if item is None:
        return None
    return healthcheck_to_docker_spec(item)


def healthcheck_to_docker_spec(item: HealthCheck) -> Dict[str, Any]:
    """
    Converts HealthCheck objects to Docker's API style
    """

    options = getattr(item, "options", None) or HealthcheckOptions()

    interval: int = 0 if options.interval == "" else duration_to_nano(options.interval)
    timeout: int = 0 if options.timeout == "" else duration_to_nano(options.timeout)
    retries: int = options.retries
    start_period: int = (
        0 if options.start_period == "" else duration_to_nano(options.start_period)
    )
    start_interval: int = (
        0 if options.start_interval == "" else duration_to_nano(options.start_interval)
    )

    if isinstance(item, InheritHealthcheck):
        return {
            "test": [],
            "interval": interval,
            "timeout": timeout,
            "retries": retries,
            "start_period": start_period,
            "start_interval": start_interval,
        }
    elif isinstance(item, NoneHealthcheck):
        return {
            "test": ["NONE"],
            "interval": 0,
            "timeout": 0,
            "retries": 0,
            "start_period": 0,
            "start_interval": 0,
        }
    elif isinstance(item, CmdHealthcheck):
        return {
            "test": ["CMD"] + item.command,
            "interval": interval,
            "timeout": timeout,
            "retries": retries,
            "start_period": start_period,
            "start_interval": start_interval,
        }

    elif isinstance(item, CmdShellHealthcheck):  # type: ignore
        return {
            "test": ["CMD-SHELL", item.command],
            "interval": interval,
            "timeout": timeout,
            "retries": retries,
            "start_period": start_period,
            "start_interval": start_interval,
        }

    raise RuntimeError(f"Unknown type of healthcheck {item}")
