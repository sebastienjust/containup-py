import argparse
import logging
import sys
from typing import List, Optional, cast

logger = logging.getLogger(__name__)

# Version is managed by bumpver. Do not touch
_version = "v0.1.5"


class Config:
    """
    Contains parsed arguments from the command line.

    Provides typed and controlled access to certain parameters,
    such as additional arguments passed through by the user.

    """

    def __init__(self, args: argparse.Namespace):
        self._args: argparse.Namespace = args
        print(args.service)

    @property
    def extra_args(self) -> List[str]:
        """Additional CLI arguments, the ones after `--`.

        Returns:
            List of strings or empty list
        """
        return self._args.extra_args or []

    @property
    def command(self) -> str:
        """Command to execute"""
        return cast(str, self._args.command) or ""

    @property
    def serviceOptional(self) -> Optional[str]:
        """Service to run command onto"""
        return cast(str, self._args.service) or None

    @property
    def service(self) -> str:
        """Service to run command onto, required"""
        if self.serviceOptional is None:
            raise RuntimeError("Service name is None")
        return self.serviceOptional

    @property
    def services(self) -> list[str]:
        """Returns service as list or empty list"""
        return self._args.service

    def validate(self) -> None:
        """Validates configuration and stops programm if there are errors"""
        if self.command == "logs":
            if self.serviceOptional is None:
                logger.error("Service name is required for command logs")
                sys.exit(1)


def containup_cli() -> Config:
    prog = sys.argv[0]
    config = containup_cli_args(prog, sys.argv[1:])
    return config


def containup_cli_args(prog: str, known_args: list[str]) -> Config:
    """
    Handles command line arguments.

    Returns:
        Configuration object containing parsed arguments and
        extra command line arguments.
    """
    parser = argparse.ArgumentParser(prog=prog)
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s using containup {_version}"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p = subparsers.add_parser("up")
    p.add_argument(
        "service", nargs="*", help="If specified, launches only those services"
    )
    p.add_argument("extra_args", nargs=argparse.REMAINDER, help="Your own arguments")

    p = subparsers.add_parser("down")
    p.add_argument("service", nargs="*", help="If specified, stops only those services")
    p.add_argument("extra_args", nargs=argparse.REMAINDER, help="Your own arguments")

    logs_parser = subparsers.add_parser("logs")
    logs_parser.add_argument("service", nargs=1, help="Get logs from service")
    p.add_argument("extra_args", nargs=argparse.REMAINDER, help="Your own arguments")

    subparsers.add_parser("export")
    p.add_argument("extra_args", nargs=argparse.REMAINDER, help="Your own arguments")

    args = parser.parse_args(args=known_args)

    config = Config(args)
    config.validate()

    return config


if __name__ == "__main__":
    print(containup_cli())
