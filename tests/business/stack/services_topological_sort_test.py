import pytest

from containup.stack.stack import (
    Service,
    services_topological_sort,
    ServiceUnknownDependencyException,
    ServiceCycleException,
)


def service(name: str, depends_on: list[str] = []) -> Service:
    return Service(name, image="dummy", depends_on=depends_on)


def test_simple_sort():
    services = [
        service("db"),
        service("redis"),
        service("api", depends_on=["db", "redis"]),
        service("frontend", depends_on=["api"]),
    ]
    sorted_names = [s.name for s in services_topological_sort(services)]
    assert sorted_names.index("db") < sorted_names.index("api")
    assert sorted_names.index("redis") < sorted_names.index("api")
    assert sorted_names.index("api") < sorted_names.index("frontend")


def test_no_dependencies():
    services = [service("a"), service("b"), service("c")]
    sorted_names = [s.name for s in services_topological_sort(services)]
    assert set(sorted_names) == {"a", "b", "c"}


def test_missing_dependency():
    services = [service("web", depends_on=["db"])]
    with pytest.raises(ServiceUnknownDependencyException):
        services_topological_sort(services)


def test_cycle_detection():
    services = [
        service("a", depends_on=["b"]),
        service("b", depends_on=["c"]),
        service("c", depends_on=["a"]),
    ]
    with pytest.raises(ServiceCycleException):
        services_topological_sort(services)


def test_empty_service_list():
    assert services_topological_sort([]) == []
