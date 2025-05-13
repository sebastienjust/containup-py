from typing import List, Union, Tuple, Dict

from containup.stack.service_ports import ServicePortMapping


def ports_to_docker_spec(
    mappings: List[ServicePortMapping],
) -> Dict[str, List[Union[int, Tuple[str, int]]]]:
    """
    Convert a list of port mappings into a Docker-compatible ports dictionary.
    """
    # Initialize an empty dictionary.
    # Each key represents a container port with protocol (e.g., "80/tcp").
    # Each value is a list of host-side bindings (integers, tuples, or None).
    result: Dict[str, List[Union[int, Tuple[str, int]]]] = {}

    for m in mappings:
        # Convert a single port mapping to a (key, value) pair
        # - key: container_port/protocol, e.g., "80/tcp"
        # - value: host port or (host_ip, host_port)
        key, value = port_to_docker_spec(m)

        # If this container port hasn't been seen yet, create a new list
        if key not in result:
            result[key] = [value]
        else:
            # If it already exists, append the new mapping to the list
            result[key].append(value)

    return result


def port_to_docker_spec(
    mapping: ServicePortMapping,
) -> Tuple[str, Union[int, Tuple[str, int]]]:
    """
    Convert a single port mapping into a Docker-compatible key/value pair.
    """
    # Compose the dictionary key as "container_port/protocol", e.g., "80/tcp"
    key = f"{mapping.container_port}/{mapping.protocol}"

    # Determine the host-side binding value:
    # - If no host_ip is provided:
    #     - Use host_port if given, otherwise fall back to container_port (means random binding)
    # - If host_ip is provided:
    #     - Use a tuple of (host_ip, host_port) or (host_ip, container_port) as fallback
    value: Union[int, Tuple[str, int]]
    if mapping.host_ip is None:
        value = mapping.host_port or mapping.container_port
    else:
        value = (mapping.host_ip, mapping.host_port or mapping.container_port)
    return key, value
