import logging
from typing import Optional

from .containup_cli import Config
from containup.infra.runner.runner import StackRunner
from .stack.stack import Stack

logger = logging.getLogger(__name__)


def containup_run(stack: Stack, config: Optional[Config] = None) -> None:
    """
    Runs commands given from the config over the stack.

    Args:
        stack: stack to run
        config: if None (most ot your use cases) command line arguments will be taken from the CLI
    """
    StackRunner(stack=stack, config=config).run()
