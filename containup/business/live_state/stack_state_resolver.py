from containup.business.commands.container_operator import ContainerOperator
from containup.business.live_state.stack_state import StackState
from containup.stack.stack import Stack


class StackStateResolver:
    def __init__(self, operator: ContainerOperator):
        self._operator = operator
        pass

    def resolve(self, stack: Stack) -> StackState:
        state = StackState()
        for network in stack.networks:
            exists = self._operator.network_exists(network.name)
            state.set_network_state(network.name, "exists" if exists else "missing")

        for volume in stack.volumes:
            exists = self._operator.volume_exists(volume.name)
            state.set_volume_state(volume.name, "exists" if exists else "missing")

        for service in stack.services:
            image = service.image
            exists = self._operator.image_exists(image)
            state.set_image_state(image, "exists" if exists else "missing")

        for service in stack.services:
            exists = self._operator.container_exists(service.container_name_safe())
            state.set_container_state(
                service.container_name_safe(), "exists" if exists else "missing"
            )

        return state
