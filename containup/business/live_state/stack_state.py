from typing import Literal

ContainerState = Literal["unknown", "exists", "missing"]
VolumeState = Literal["unknown", "exists", "missing"]
NetworkState = Literal["unknown", "exists", "missing"]
ImageState = Literal["unknown", "exists", "missing"]


class StackState:
    """
    Contains known states from volumes, containers, networks and images.

    Maintains a map between unique identifiers and resolved states.
    If an object is not in the map, it means that its state is unknown.
    Unknown can mean that nobody checked the state or that state checking
    resolved to unknown.
    """

    def __init__(self):
        self._container_states: dict[str, ContainerState] = {}
        self._volume_states: dict[str, VolumeState] = {}
        self._network_states: dict[str, NetworkState] = {}
        self._image_states: dict[str, ImageState] = {}

    def get_container_state(self, container_id: str) -> ContainerState:
        return self._container_states.get(container_id, "unknown")

    def set_container_state(self, container_id: str, state: ContainerState):
        self._container_states[container_id] = state

    def get_volume_state(self, volume_id: str) -> ContainerState:
        return self._volume_states.get(volume_id, "unknown")

    def set_volume_state(self, volume_id: str, state: VolumeState):
        self._volume_states[volume_id] = state

    def get_network_state(self, network_id: str) -> ContainerState:
        return self._network_states.get(network_id, "unknown")

    def set_network_state(self, network_id: str, state: NetworkState):
        self._network_states[network_id] = state

    def get_image_state(self, image_id: str) -> ContainerState:
        return self._image_states.get(image_id, "unknown")

    def set_image_state(self, image_id: str, state: ImageState):
        self._image_states[image_id] = state

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"containers={self._container_states}, "
            f"volumes={self._volume_states}, "
            f"networks={self._network_states}, "
            f"images={self._image_states})"
        )
