from containup import (
    InheritHealthcheck,
    HealthcheckOptions,
    NoneHealthcheck,
    CmdShellHealthcheck,
    CmdHealthcheck,
)
from containup.infra.docker.healthcheck import (
    healthcheck_to_docker_spec,
    healthcheck_to_docker_spec_unsafe,
)


def test_healthcheck_inherit():
    res = healthcheck_to_docker_spec(
        InheritHealthcheck(
            options=HealthcheckOptions(
                interval="10s",
                timeout="100ms",
                retries=10,
                start_period="100s",
                start_interval="50s",
            )
        )
    )
    assert res["test"] == []
    assert res["interval"] == 10_000_000_000
    assert res["timeout"] == 100_000_000
    assert res["retries"] == 10
    assert res["start_period"] == 100_000_000_000
    assert res["start_interval"] == 50_000_000_000


def test_healthcheck_none():
    res = healthcheck_to_docker_spec(NoneHealthcheck())
    assert res["test"] == ["NONE"]
    assert res["interval"] == 0
    assert res["timeout"] == 0
    assert res["retries"] == 0
    assert res["start_period"] == 0
    assert res["start_interval"] == 0


def test_healthcheck_cmdshell():
    res = healthcheck_to_docker_spec(
        CmdShellHealthcheck(
            command="my command",
            options=HealthcheckOptions(
                interval="10s",
                timeout="100ms",
                retries=10,
                start_period="100s",
                start_interval="50s",
            ),
        )
    )

    assert res["test"] == ["CMD-SHELL", "my command"]
    assert res["interval"] == 10_000_000_000
    assert res["timeout"] == 100_000_000
    assert res["retries"] == 10
    assert res["start_period"] == 100_000_000_000
    assert res["start_interval"] == 50_000_000_000


def test_healthcheck_cmd():
    res = healthcheck_to_docker_spec(
        CmdHealthcheck(
            command=["my", "command"],
            options=HealthcheckOptions(
                interval="10s",
                timeout="100ms",
                retries=10,
                start_period="100s",
                start_interval="50s",
            ),
        )
    )

    assert res["test"] == ["CMD", "my", "command"]
    assert res["interval"] == 10_000_000_000
    assert res["timeout"] == 100_000_000
    assert res["retries"] == 10
    assert res["start_period"] == 100_000_000_000
    assert res["start_interval"] == 50_000_000_000


def test_healthcheck_default_parameters():
    res = healthcheck_to_docker_spec(
        CmdHealthcheck(
            command=["my", "command"],
            options=HealthcheckOptions(),
        )
    )

    assert res["test"] == ["CMD", "my", "command"]
    assert res["interval"] == 0
    assert res["timeout"] == 0
    assert res["retries"] == 0
    assert res["start_period"] == 0
    assert res["start_interval"] == 0


def test_healthcheck_no_options():
    res = healthcheck_to_docker_spec(
        CmdHealthcheck(
            command=["my", "command"],
        )
    )

    assert res["test"] == ["CMD", "my", "command"]
    assert res["interval"] == 0
    assert res["timeout"] == 0
    assert res["retries"] == 0
    assert res["start_period"] == 0
    assert res["start_interval"] == 0


def test_healthcheck_unsafe_none():
    res = healthcheck_to_docker_spec_unsafe(None)
    assert res is None
