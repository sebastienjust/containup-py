from containup.cli import containup_cli_args


# Tests for up
# --------------


def test_given_up__when_cli__then_up_and_no_service() -> None:
    args = containup_cli_args("myprog", ["up"])
    assert args.command == "up"
    assert args.services == []


def test_given_up__when_cli__then_up_and_service_found() -> None:
    args = containup_cli_args("myprog", ["up", "--service", "myservice"])
    assert args.services == ["myservice"]


def test_given_up_with_extra_args__when_cli__then_up_and_args_found() -> None:
    args = containup_cli_args(
        "myprog",
        [
            "up",
            "--",
            "--myextra=toto",
            "--myotherextra=tutu",
        ],
    )
    assert args.services == []
    assert args.extra_args == ["--myextra=toto", "--myotherextra=tutu"]


def test_given_up_with_extra_args__when_cli__then_up_and_one_service_and_args_found() -> (
    None
):
    args = containup_cli_args(
        "myprog",
        [
            "up",
            "--service",
            "myservice",
            "--",
            "--myextra=toto",
            "--myotherextra=tutu",
        ],
    )
    assert args.services == ["myservice"]
    assert args.extra_args == ["--myextra=toto", "--myotherextra=tutu"]


def test_given_up_with_extra_args__when_cli__then_up_and_services_and_args_found() -> (
    None
):
    args = containup_cli_args(
        "myprog",
        [
            "up",
            "--service",
            "myservice",
            "myotherservice",
            "--",
            "--myextra=toto",
            "--myotherextra=tutu",
        ],
    )
    assert args.services == ["myservice", "myotherservice"]
    assert args.extra_args == ["--myextra=toto", "--myotherextra=tutu"]


def test_given_up__when_cli__then_up_and_services_found() -> None:
    assert containup_cli_args(
        "myprog", ["up", "--service", "myservice", "myotherservice"]
    ).services == ["myservice", "myotherservice"]


# Tests for down
# --------------


def test_given_down__when_cli__then_down_and_no_service() -> None:
    args = containup_cli_args("myprog", ["down"])
    assert args.command == "down"
    assert args.services == []


def test_given_down__when_cli__then_down_and_service_found() -> None:
    args = containup_cli_args("myprog", ["down", "--service=myservice"])
    assert args.command == "down"
    assert args.services == ["myservice"]


def test_given_down__when_cli__then_down_and_services_found() -> None:
    args = containup_cli_args(
        "myprog", ["down", "--service", "myservice", "myotherservice"]
    )
    assert args.command == "down"
    assert args.services == ["myservice", "myotherservice"]


def test_given_down_with_extra_args__when_cli__then_up_and_one_service_and_args_found() -> (
    None
):
    args = containup_cli_args(
        "myprog",
        [
            "down",
            "--service",
            "myservice",
            "--",
            "--myextra=toto",
            "--myotherextra=tutu",
        ],
    )
    assert args.services == ["myservice"]
    assert args.extra_args == ["--myextra=toto", "--myotherextra=tutu"]


def test_given_down_with_extra_args__when_cli__then_up_and_services_and_args_found() -> (
    None
):
    args = containup_cli_args(
        "myprog",
        [
            "down",
            "--service",
            "myservice",
            "myotherservice",
            "--",
            "--myextra=toto",
            "--myotherextra=tutu",
        ],
    )
    assert args.services == ["myservice", "myotherservice"]
    assert args.extra_args == ["--myextra=toto", "--myotherextra=tutu"]


def test_given_down__when_cli__then_up_and_services_found() -> None:
    assert containup_cli_args(
        "myprog", ["down", "--service", "myservice", "myotherservice"]
    ).services == ["myservice", "myotherservice"]
