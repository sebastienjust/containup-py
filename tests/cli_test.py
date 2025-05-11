from containup.cli import containup_cli_args


def test_given_up__when_cli__then_up_and_no_service() -> None:
    assert containup_cli_args("myprog", ["up"]).command == "up"
    assert containup_cli_args("myprog", ["up"]).services == []


def test_given_up__when_cli__then_up_and_service_found() -> None:
    assert containup_cli_args("myprog", ["up", "myservice"]).services == ["myservice"]


def test_given_up__when_cli__then_up_and_services_found() -> None:
    assert containup_cli_args(
        "myprog", ["up", "myservice", "myotherservice"]
    ).services == ["myservice", "myotherservice"]


def test_given_down__when_cli__then_up_and_no_service() -> None:
    assert containup_cli_args("myprog", ["down"]).command == "down"
    assert containup_cli_args("myprog", ["down"]).services == []


def test_given_down__when_cli__then_up_and_service_found() -> None:
    assert containup_cli_args("myprog", ["down", "myservice"]).services == ["myservice"]


def test_given_down__when_cli__then_up_and_services_found() -> None:
    assert containup_cli_args(
        "myprog", ["down", "myservice", "myotherservice"]
    ).services == ["myservice", "myotherservice"]
