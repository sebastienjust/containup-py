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

    @property
    def extra_args(self) -> List[str]:
        """Additional CLI arguments, the ones after `--`.

        Returns:
            List of strings or empty list
        """
        extra_args: List[str] = self._args.extra_args
        extra: List[str] = (
            (extra_args or [])[1:]
            if (extra_args or [])[:1] == ["--"]
            else (extra_args or [])
        )
        return extra

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
        return self._args.service or []

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

    up_parser = subparsers.add_parser("up")
    up_parser.add_argument(
        "--service",
        nargs="*",
        help="If specified, launches only those services",
    )
    _add_extra_args(up_parser)

    down_parser = subparsers.add_parser("down")
    down_parser.add_argument(
        "--service", nargs="*", help="If specified, stops only those services"
    )
    _add_extra_args(down_parser)

    logs_parser = subparsers.add_parser("logs")
    logs_parser.add_argument("--service", help="Get logs from service", required=True)
    _add_extra_args(logs_parser)

    export_parser = subparsers.add_parser("export")
    _add_extra_args(export_parser)

    args = parser.parse_args(args=known_args)
    config = Config(args)
    config.validate()

    print("Namespace: ", args)

    return config


def _add_extra_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "extra_args", nargs=argparse.REMAINDER, help="Your own arguments"
    )


if __name__ == "__main__":
    #
    # Tool to debug command line parsing
    #
    # Just an example of reading the CLI and extracting additional
    # parameters
    #

    # call our CLI parser
    containup_config = containup_cli()

    # get your extra arguments (it's a list of string like sys.argv[:1])
    script_extra_args = containup_config.extra_args

    # Then, you can parse them with, for example, Python's argparse :
    sub_parser = argparse.ArgumentParser(prog="mystack")
    sub_parser.add_argument("--origin_name")
    sub_parser.add_argument("--origin_version")

    parsed = sub_parser.parse_args(args=script_extra_args)
    print("origin_name=", parsed.origin_name)
    print("origin_name=", parsed.origin_version)
