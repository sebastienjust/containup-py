import sys
from abc import abstractmethod
from typing import Optional, TextIO


class ExecutionAuditor:
    @abstractmethod
    def record(self, message: str) -> None:
        pass

    @abstractmethod
    def flush(self) -> None:
        pass


class StdoutAuditor(ExecutionAuditor):
    def __init__(self, stream: Optional[TextIO] = None):
        self._messages: list[str] = []
        self._stream: TextIO = stream or sys.stdout

    def record(self, message: str) -> None:
        self._messages.append(message)

    def flush(self) -> None:
        for msg in self._messages:
            print(msg, file=self._stream)
