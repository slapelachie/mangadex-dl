"""
Random utilities for mangadex_dl
"""
import re
import shutil
import os
import logging
import time
import io
from time import sleep, time
from typing import Dict
from math import floor
from datetime import date

import requests
from dict2xml import dict2xml
from PIL import Image, ImageFile

from mangadex_dlz.typehints import ChapterInfo, SeriesInfo
from mangadex_dlz.logger_utils import TqdmLoggingHandler
from mangadex_dlz.mangadex_report import MangadexReporter

logger = logging.getLogger(__name__)
logger.addHandler(TqdmLoggingHandler())
logger.propagate = False

reporter = MangadexReporter()


def is_url(url: str) -> bool:
    """
    Determine if a string is a URL

    Arguments:
        url (str): the string to test

    Returns:
        (bool): true if the string is a valid url, false otherwise
    """
    return bool(
        re.match(
            r"^(?:http(s)?:\/\/)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+$",
            url,
        )
    )


def get_mangadex_request(url: str) -> requests.Response:
    """
    Perform a request to the mangadex server with the appropiate rules in place (rate limiting etc)

    Arguments:
        url (str): the url to perform the request on
        rate (int): the rate at which requests can be made measured in images per minute

    Returns:
        (requests.Response): the response from the server

    Raises:
        (requests.HTTPError): if the url does not return a valid response
    """
    response = requests.get(url, timeout=90)

    while response.status_code == 429:
        wait_time = int(
            int(response.headers.get("x-ratelimit-retry-after", int(time() + 60)))
            - time()
        )

        logger.warning("Exceeded rate-limit, waiting %i seconds", wait_time)
        sleep(wait_time)

        response = requests.get(url, timeout=90)

    if response.status_code != 200:
        response.raise_for_status()

    rate_limit = int(response.headers.get("x-ratelimit-limit") or 0)
    if rate_limit != 0:
        sleep(60 / rate_limit)

    return response


def get_mangadex_response(url: str) -> Dict:
    """
    Gets the response from get_mangadex_request but in the json format
    I wrote a lot of code relying on this before I moved it to the afformentioned function, and
    didn't want to update all the references

    Arguments:
        url (str): the url to perform the request to
        rate (int): the rate at which requests can be made

    Returns:
        (Dict?): the response in json format
    """
    response = get_mangadex_request(url)
    return response.json()


def create_cbz(chapter_directory: str):
    """
    Creates a CBZ archive (just a zip archive) for the given folder

    Arguments:
        chapter_directory (str): the directory to turn into a CBZ
    """
    if not os.path.isdir(chapter_directory):
        raise NotADirectoryError("The supplied path is not a directory!")

    try:
        shutil.make_archive(chapter_directory, "zip", chapter_directory)
    except shutil.Error as err:
        raise OSError(f"Failed to make archive for {chapter_directory}.zip") from err

    try:
        shutil.move(
            f"{chapter_directory}.zip",
            f"{chapter_directory}.cbz",
        )
    except shutil.Error as err:
        raise OSError(
            f"Failed to rename archive from {chapter_directory}.zip to {chapter_directory}.cbz"
        ) from err


def create_comicinfo(output_directory: str, chapter: ChapterInfo, series: SeriesInfo):
    """
    Creates a ComicInfo file for the chapter, only tested with Komago, so I have no idea if this
    works elsewhere

    Arguments:
        output_directory (str): the directory to save the file
        chapter (ChapterInfo): the chapter information (see mangadex_dlz.chapter.get_chapter_info)
        series (SeriesInfo): the series information (see mangadex_dlz.series.get_series_info)

    Raises:
        KeyError: if one of the keys in the parsed dictionary does not exist
        OSError: if the ComicInfo.xml file could not be created
    """
    if not all(key in chapter for key in ["title", "chapter"]) or not all(
        key in series for key in ["title", "description", "year", "author"]
    ):
        raise KeyError(
            "One of the needed fields in the parsed dictionaries is not valid!"
        )

    series_year = series.get("year", date.today().year) or date.today().year

    data = {
        "ComicInfo": {
            "Title": chapter.get("title"),
            "Series": series.get("title"),
            "Summary": series.get("description"),
            "Number": f'{chapter.get("chapter"):.1f}'.rstrip("0").rstrip("."),
            "Year": series_year,
            "Writer": series.get("author"),
            "Manga": "YesAndRightToLeft",
        }
    }
    xml = dict2xml(data)

    try:
        with open(
            os.path.join(output_directory, "ComicInfo.xml"), "w+", encoding="utf-8"
        ) as fout:
            fout.write(xml)
    except OSError as err:
        raise OSError(
            f'Could not open "{os.path.join(output_directory, "ComicInfo")}" for writing'
        ) from err


def download_image(
    url: str, path: str, max_height: int = 2400, enable_reporting: bool = False
):
    """
    Download the image from the given url to the specified path
    Image is converted to RGB, downscaled to a height of max_height pixels if it exceeds this
    height, and then saved as a to the given path

    The download and saving is attempted 5 times before aborting, this is because there was a time
    where pillow complained about the image being truncated, and on the next attempt it was fine

    Arguments:
        url (str): the url of the mangadex chapter image (page)
        path (str): the output destination of the downloaded image
        max_height (int): the maximum height
        enable_reporting (bool): if reports on server health should be sent

    Raises:
        OSError: if the image has any trouble saving or downloading
    """
    ImageFile.LOAD_TRUNCATED_IMAGES = False
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Attempt download 5 times
    for attempt in range(5):
        if attempt > 0:
            logger.warning(
                "Download for %s failed, retrying (attempt %i/5)", url, attempt
            )

        try:
            image = get_image_data(url, max_height, enable_reporting)
            if image is None:
                continue

            image.save(path, quality=90)
            break
        except OSError:
            # Very rare occasions the image acts up and this setting needs to be applied, see
            # https://uploads.mangadex.org/data/7bc61df1775d46f3cd9fd7501860f09b/\
            # 16-5dd67abf9dca4240d20eebe3f4780b1ffba5a9c90b9067def5b9f4806eb93f25.png
            ImageFile.LOAD_TRUNCATED_IMAGES = True
            continue

    else:
        raise OSError("Failed to download and save image!")


def get_image_data(url: str, max_height: int, enable_reporting: bool) -> Image:
    """
    Get image data from URL in PIL.Image format

    Arguments:
        url (str): the url to get the image data from
        max_height (int): the maximum height of the image, downscaled if too tall
        enable_reporting (bool): if reports on server health should be sent

    Returns:
        (Pil.Image.Image): the PIL image
    """
    success = False
    try:
        response = get_mangadex_request(url)
        success = True
    except (requests.HTTPError, requests.Timeout):
        success = False
    finally:
        if enable_reporting:
            report = {
                "url": url,
                "success": success,
                "bytes": len(response.content),
                "cached": response.headers.get("X-Cache") == "HIT",
                "duration": int(response.elapsed.total_seconds() * 1000),
            }
            reporter.add_report(report)

    if not success:
        return None

    image = Image.open(io.BytesIO(response.content))
    image = image.convert("RGB")

    # Downscale if too big
    width, height = image.size
    if height > max_height:
        logger.debug(
            'Image height from "%s" is greater than %d pixels, downscaling...',
            url,
            max_height,
        )
        ratio = width / height
        new_width = floor(ratio * max_height)
        image = image.resize((new_width, max_height), Image.BICUBIC)

    return image


def make_name_safe(name: str) -> str:
    """
    Replaces any character that is not a word, - (dash), _ (underscore), . (period) or space (  )
    with a _ (underscore) from the name to make it useable for folder and file names
    """
    return re.sub(r"[^\w\-_\. ]", "_", name)


def is_number(number: str):
    """Checks if the supplied string is a number"""
    try:
        float(number)
        return True
    except ValueError:
        return False
