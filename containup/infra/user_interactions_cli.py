from containup.commands.user_interactions import UserInteractions
import sys


class UserInteractionsCLI(UserInteractions):
    """Real implementation of the user interactions with CLI."""

    def exit_with_error(self, error_code: int):
        sys.exit(error_code)
