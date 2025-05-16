import logging
from typing import List, Optional, Union

from .network import Network
from .service import Service
from .volume import Volume

# Initialize logger for this lib. Don't force the logger
logger = logging.getLogger(__name__)

StockItem = Union[Service, Volume, Network]


class Stack:
    def __init__(self, name: str):
        self.name = name

        self.mounts: dict[str, Volume] = {}
        self.networks: dict[str, Network] = {}
        self.services: list[Service] = []

    def add(self, item_or_list: Union[StockItem, List[StockItem]]):
        items = item_or_list if isinstance(item_or_list, list) else [item_or_list]
        for item in items:
            logger.debug(item)
            if isinstance(item, Service):
                self.services.append(item)
            elif isinstance(item, Volume):
                self.mounts[item.name] = item
            elif isinstance(item, Network):  # type: ignore
                self.networks[item.name] = item
        return self

    def get_services_sorted(
        self, filter_services: Optional[List[str]] = None
    ) -> list[Service]:
        """
        Returns a list of services filtered by filter_services and with topological sort.

        If filter_services is None, the services will not be filtered.
        If filter_services is an empty list, the services will not be filtered.
        Otherwise, the services returned should match the given filter_services list.

        Arguments:
            filter_services (list[str]) list of names of services
        """
        # if filter_services is empty or None then ignore it
        # otherwise filter services to run to match filter_services (only the services the user wants to run)
        targets: list[Service] = (
            self.services
            if not filter_services
            else [
                service for service in self.services if service.name in filter_services
            ]
        )
        sorted_services = services_topological_sort(targets)
        return sorted_services


def services_topological_sort(services: list[Service]) -> list[Service]:
    name_to_service = {s.name: s for s in services}
    visited: set[str] = set()
    temp_mark: set[str] = set()
    result: list[Service] = []

    def visit(service: Service):
        if service.name in visited:
            return
        if service.name in temp_mark:
            raise ServiceCycleException(f"Cycle detected involving: {service.name}")
        temp_mark.add(service.name)
        for dep in service.depends_on:
            if dep not in name_to_service:
                raise ServiceUnknownDependencyException(
                    f"Unknown dependency '{dep}' required by '{service.name}'"
                )
            visit(name_to_service[dep])
        temp_mark.remove(service.name)
        visited.add(service.name)
        result.append(service)

    for s in services:
        visit(s)

    return result


class ServiceCycleException(Exception):
    pass


class ServiceUnknownDependencyException(Exception):
    pass
