from containup.business.commands.user_interactions import UserInteractions
import sys
import time


class UserInteractionsCLI(UserInteractions):
    """Real implementation of the user interactions with CLI."""

    def exit_with_error(self, error_code: int):
        sys.exit(error_code)

    def time(self) -> float:
        return time.time()

    def sleep(self, seconds: float) -> None:
        return time.sleep(seconds)
