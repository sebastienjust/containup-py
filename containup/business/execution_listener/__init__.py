from abc import ABC, abstractmethod
from dataclasses import dataclass

from containup.stack.network import Network
from containup.stack.stack import Service
from containup.stack.volume import Volume


@dataclass
class ExecutionEvt(ABC):
    pass


@dataclass
class ExecutionEvtVolume(ExecutionEvt):
    volume_id: str


@dataclass
class ExecutionEvtVolumeExistsCheck(ExecutionEvtVolume):
    volume_id: str
    exists: bool


@dataclass
class ExecutionEvtVolumeRemoved(ExecutionEvtVolume):
    volume_id: str


@dataclass
class ExecutionEvtVolumeCreated(ExecutionEvtVolume):
    volume_id: str
    volume: Volume


@dataclass
class ExecutionEvtContainer(ExecutionEvt):
    container_id: str


@dataclass
class ExecutionEvtContainerExistsCheck(ExecutionEvtContainer):
    container_id: str
    exists: bool


@dataclass
class ExecutionEvtContainerRemoved(ExecutionEvtContainer):
    container_id: str


@dataclass
class ExecutionEvtContainerRun(ExecutionEvtContainer):
    container_id: str
    container: Service


@dataclass
class ExecutionEvtNetwork(ExecutionEvt):
    network_id: str


@dataclass
class ExecutionEvtNetworkExistsCheck(ExecutionEvtNetwork):
    network_id: str
    exists: bool


@dataclass
class ExecutionEvtNetworkRemoved(ExecutionEvtNetwork):
    network_id: str


@dataclass
class ExecutionEvtNetworkCreated(ExecutionEvtNetwork):
    network_id: str
    network: Network


class ExecutionListener:
    @abstractmethod
    def record(self, message: ExecutionEvt) -> None:
        pass

    @abstractmethod
    def get_events(self) -> list[ExecutionEvt]:
        pass


class ExecutionListenerStd(ExecutionListener):

    def __init__(self):
        self._messages: list[ExecutionEvt] = []

    def record(self, message: ExecutionEvt) -> None:
        self._messages.append(message)

    def get_events(self) -> list[ExecutionEvt]:
        return self._messages
