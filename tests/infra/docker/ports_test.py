from containup.stack.service_ports import ServicePortMapping
from containup.infra.docker.ports import ports_to_docker_spec


def test_simple_mapping():
    mapping = [ServicePortMapping(container_port=80, host_port=8080)]
    assert ports_to_docker_spec(mapping) == {"80/tcp": [8080]}


def test_random_host_port():
    mapping = [ServicePortMapping(container_port=80)]
    assert ports_to_docker_spec(mapping) == {"80/tcp": [80]}  # Docker assigns random


def test_specific_ip_and_port():
    mapping = [
        ServicePortMapping(container_port=80, host_port=8080, host_ip="127.0.0.1")
    ]
    assert ports_to_docker_spec(mapping) == {"80/tcp": [("127.0.0.1", 8080)]}


def test_multiple_bindings_same_port():
    mapping = [
        ServicePortMapping(container_port=80, host_port=8080),
        ServicePortMapping(container_port=80, host_port=8081),
    ]
    assert ports_to_docker_spec(mapping) == {"80/tcp": [8080, 8081]}


def test_multiple_protocols():
    mapping = [
        ServicePortMapping(container_port=80, host_port=8080, protocol="tcp"),
        ServicePortMapping(container_port=80, host_port=8081, protocol="udp"),
    ]
    assert ports_to_docker_spec(mapping) == {
        "80/tcp": [8080],
        "80/udp": [8081],
    }


def test_host_ip_with_default_container_port():
    mapping = [ServicePortMapping(container_port=1234, host_ip="127.0.0.1")]
    assert ports_to_docker_spec(mapping) == {"1234/tcp": [("127.0.0.1", 1234)]}
