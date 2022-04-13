import os
import argparse
import sys

from mangadex_dl import MangaDexDL


def get_args():
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
    arg.add_argument("url", help="url to download")

    return arg


def parse_args(parser: argparse.ArgumentParser):
    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()
        sys.exit(1)

    mangadex = MangaDexDL(
        os.path.realpath(args.cache_file), os.path.realpath(args.out_directory)
    )
    mangadex.handle_url(args.url)


def main():
    parser = get_args()
    parse_args(parser)


if __name__ == "__main__":
    main()
