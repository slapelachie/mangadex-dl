"""The main module"""
import os
import argparse
import sys
import logging

from mangadex_dlz import __version__, __copyright__
from mangadex_dlz import MangaDexDL, TqdmLoggingHandler


logger = logging.getLogger(__name__)
logger.addHandler(TqdmLoggingHandler())
logger.propagate = False


def get_args() -> argparse.ArgumentParser:
    """
    Gets the arguments through argparse

    Returns:
        (argparse.ArgumentParser): the arguments
    """
    arg = argparse.ArgumentParser(
        description="Download mangadex manga from the command line"
    )

    arg.add_argument("--version", action="store_true", help="Print version information")
    arg.add_argument(
        "--progress", action="store_true", help="Display progress bars for the download"
    )
    arg.add_argument("--debug", action="store_true", help="Debug Logging")
    arg.add_argument("-v", "--verbose", action="store_true", help="verbose logging")
    arg.add_argument(
        "-o",
        "--out-directory",
        help="Output directory for series, defaults to ./mangadex-dl",
        default=os.path.realpath("./mangadex-dl"),
    )
    arg.add_argument(
        "--cache-file",
        default=os.path.expandvars("$HOME/.cache/mangadex-dl/downloaded.json"),
    )
    arg.add_argument(
        "--override", action="store_true", help="Ignores any UUIDs in the cache file"
    )
    arg.add_argument(
        "--download-cover", action="store_true", help="Download the cover art"
    )
    arg.add_argument(
        "--download-chapter-covers",
        action="store_true",
        help="Download only the covers for the chapters of the given series/chapter",
    )
    arg.add_argument(
        "--report",
        action="store_true",
        help="Allow telementary to mangadex for reporting the health of the used servers, "
        "may increase download times",
    )
    arg.add_argument("url", help="URL of series/chapter to download", nargs="?")

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

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    elif args.verbose:
        logging.basicConfig(level=logging.INFO)

    mangadex = MangaDexDL(
        os.path.realpath(args.cache_file),
        os.path.realpath(args.out_directory),
        override=args.override,
        download_cover=args.download_cover,
        progress_bars=args.progress,
        reporting=args.report,
    )

    if args.download_chapter_covers:
        mangadex.download_covers(args.url)
    else:
        mangadex.download(args.url)


def main():
    parser = get_args()
    parse_args(parser)


if __name__ == "__main__":
    main()
