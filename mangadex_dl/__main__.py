import os
import re
import argparse
import sys

from mangadex_dl.chapter import Chapter, get_chapter_cache
from mangadex_dl.series import Series


def is_url(url: str):
    return re.match(
        r"^(?:http(s)?:\/\/)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+$",
        url,
    )


def is_mangadex_url(url: str):
    return re.match(
        r"^(?:http(s)?:\/\/)?mangadex\.org\/([\w\-/?#&=]+)?",
        url,
    )


def get_mangadex_resource(url: str):
    search = re.search(
        r"^((http[s]?|ftp):\/)?\/?([^:\/\s]+)((\/\w+)*\/)([\w\-\.]+[^#?\s]+)(.*)?(#[\w\-]+)?$",
        url,
    )
    mangadex_type = search.group(4).replace("/", "")

    resource = re.search(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", url
    ).group(0)

    return [mangadex_type, resource]


def process_series(series_id: str, output_directory: str):
    series = Series(series_id)
    chapter_cache = get_chapter_cache()

    for chapter in series.get_chapters():
        if chapter.get_id() not in chapter_cache:
            chapter.download(output_directory)


def handle_mangadex_url(url: str, output_directory: str):
    mangadex_type, resource_id = get_mangadex_resource(url)

    if mangadex_type == "title":
        process_series(resource_id, output_directory)
    elif mangadex_type == "chapter":
        chapter = Chapter(resource_id)
        chapter.download(output_directory)


def get_args():
    arg = argparse.ArgumentParser(
        description="Download mangadex manga from the command line"
    )

    arg.add_argument("-v", "--verbose", action="store_true", help="verbose logging")
    arg.add_argument(
        "-o",
        "--output",
        help="output directory for volumes, defaults to ./mangadex-dl",
        default=os.path.realpath("./mangadex-dl"),
    )
    arg.add_argument("url", help="url to download")

    return arg


def parse_args(parser: argparse.ArgumentParser):
    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()
        sys.exit(1)

    if args.output:
        os.makedirs(os.path.realpath(args.output), exist_ok=True)

    if is_url(args.url):
        if not is_mangadex_url(args.url):
            sys.exit(1)

        handle_mangadex_url(args.url, os.path.realpath(args.output))


def main():
    parser = get_args()
    parse_args(parser)


if __name__ == "__main__":
    main()
