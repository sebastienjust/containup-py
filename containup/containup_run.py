import logging
from typing import Optional

from .containup_cli import Config
from containup.infra.runner.runner import StackRunner
from .stack.stack import Stack

logger = logging.getLogger(__name__)


def containup_run(
    stack: Stack, config: Optional[Config] = None, debug: bool = False
) -> None:
    """
    Runs commands given from the config over the stack.

    Args:
        stack: stack to run
        config: if None (most ot your use cases) command line arguments will be taken from the CLI
        debug: to activate debug automatically (in case you don't have already configured a logger)
    """
    ensure_logging_configured(debug)
    StackRunner(stack=stack, config=config).run()


def ensure_logging_configured(debug: bool = False) -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(name)s [%(levelname)s] %(message)s",
        )
        logging.getLogger("containup").setLevel(
            logging.DEBUG if debug else logging.INFO
        )
