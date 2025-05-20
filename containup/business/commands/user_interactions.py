from abc import ABC, abstractmethod


class UserInteractions(ABC):
    """
    User interactions are abstracted here to avoid doing system calls or exits outside the
    real runtime environment. Allow accessing system level stuff but been able to test anyway.
    (rule: no infra in business code)
    """

    @abstractmethod
    def exit_with_error(self, error_code: int):
        pass
