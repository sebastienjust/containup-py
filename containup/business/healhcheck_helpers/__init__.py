from typing import Optional

from containup.stack.service_healthcheck import (
    HealthcheckOptions,
    CmdShellHealthcheck,
    CmdHealthcheck,
)

default_options = HealthcheckOptions(
    interval="10s",  # ➤ verification frequency (reasonable, not too much)
    timeout="5s",  # ➤ max time before command says "timeout"
    retries=3,  # ➤ 3 consecutive checks means "unhealthy"
    start_period="5s",  # ➤ startup application time, let's put 5s which is average
)


def check_http_code_with_bash_grep(
    port: int,
    url: str,
    check_string: str = "200 OK",
    options: Optional[HealthcheckOptions] = default_options,
) -> CmdShellHealthcheck:
    """
    Creates a health check using bash and grep (no curl).

    This is the horror:
    `bash -c "exec 3<>/dev/tcp/127.0.0.1/{port} && echo -e 'GET {url} HTTP/1.1\r\nHost: localhost\r\n\r\n' >&3 && grep -q '{check_string}' <&3"`

    Provided so you don't have to remember it
    """
    cmd = f"""bash -c "exec 3<>/dev/tcp/127.0.0.1/{port} && echo -e 'GET {url} HTTP/1.1\r\nHost: localhost\r\n\r\n' >&3 && grep -q '{check_string}' <&3" """
    return CmdShellHealthcheck(cmd, options or default_options)


def check_postgres(
    user: str, options: Optional[HealthcheckOptions] = default_options
) -> CmdHealthcheck:
    """Standard postgresql check"""
    return CmdHealthcheck(["pg_isready", "-U", user], options or default_options)


def check_redis(
    options: Optional[HealthcheckOptions] = default_options,
) -> CmdHealthcheck:
    """Standard redis check"""
    return CmdHealthcheck(["redis-cli", "ping"], options or default_options)
