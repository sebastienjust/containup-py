import argparse
import logging
import sys
from typing import List, cast

logger = logging.getLogger(__name__)

# Version is managed by bumpver. Do not touch
_version = "v0.1.9"


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
    def services(self) -> list[str]:
        """Returns service as list or empty list"""
        return self._args.service or []

    @property
    def dry_run(self) -> bool:
        """Returns whether or not to execute the command in dry-run mode"""
        return bool(getattr(self._args, "dry_run", False))

    def __repr__(self) -> str:
        return (
            f"Config(command={self.command!r}, "
            f"services={self.services!r}, "
            f"dry_run={self.dry_run!r}, "
            f"extra_args={self.extra_args!r}, "
            f"args={self._args!r})"
        )


def containup_cli() -> Config:
    """
    Read command line arguments and return a configuration object with list of instructions to execute
    and tools to parse command arguments.

    Returns:
        Config containing parsed command line arguments
    """
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
    _add_dry_run(up_parser)
    up_parser.add_argument(
        "--service",
        nargs="*",
        help="If specified, launches only those services",
    )
    _add_extra_args(up_parser)

    down_parser = subparsers.add_parser("down")
    _add_dry_run(down_parser)
    down_parser.add_argument(
        "--service", nargs="*", help="If specified, stops only those services"
    )
    _add_extra_args(down_parser)

    args = parser.parse_args(args=known_args)
    config = Config(args)

    return config


def _add_dry_run(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="If specified, launch command in dry-run mode",
    )


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
    print(containup_config)

    # get your extra arguments (it's a list of string like sys.argv[:1])
    script_extra_args = containup_config.extra_args

    # Then, you can parse them with, for example, Python's argparse :
    sub_parser = argparse.ArgumentParser(prog="mystack")
    sub_parser.add_argument("--origin_name")
    sub_parser.add_argument("--origin_version")

    parsed = sub_parser.parse_args(args=script_extra_args)
    print("origin_name=", parsed.origin_name)
    print("origin_version=", parsed.origin_version)
