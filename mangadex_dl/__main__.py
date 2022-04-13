"""The main module"""
import os
import argparse
import sys

from mangadex_dl import __version__, __copyright__
from mangadex_dl import MangaDexDL


def get_args() -> argparse.ArgumentParser:
    """
    Gets the arguments through argparse

    Returns:
        (argparse.ArgumentParser): the arguments
    """
    arg = argparse.ArgumentParser(
        description="Download mangadex manga from the command line"
    )

    arg.add_argument("-v", "--verbose", action="store_true", help="verbose logging")
    arg.add_argument(
        "-o",
        "--out-directory",
        help="output directory for volumes, defaults to ./mangadex-dl",
        default=os.path.realpath("./mangadex-dl"),
    )
    arg.add_argument(
        "--cache-file",
        default=os.path.expandvars("$HOME/.cache/mangadex-dl/downloaded.json"),
    )
    arg.add_argument(
        "--override", action="store_true", help="Ignores any UUIDs in the cache file"
    )
    arg.add_argument("--version", action="store_true", help="Print version information")
    arg.add_argument("url", help="url to download", nargs="?")

    return arg


def parse_args(parser: argparse.ArgumentParser):
    """
    parse the arguments through the given parser

    Arguments:
        parser (argparse.ArgumentParser): the argument parser
    """
    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()
        sys.exit(1)

    if args.version:
        print(f"mangadex-dl {__version__}\n{__copyright__}")
        sys.exit(0)

    if not args.url:
        parser.print_usage()
        print("The following arguments are required: url")
        sys.exit(1)

    mangadex = MangaDexDL(
        os.path.realpath(args.cache_file),
        os.path.realpath(args.out_directory),
        override=args.override,
    )
    mangadex.handle_url(args.url)


def main():
    parser = get_args()
    parse_args(parser)


if __name__ == "__main__":
    main()
