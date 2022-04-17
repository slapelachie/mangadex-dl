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
from typing import Dict, Tuple, TypedDict
from math import floor
from datetime import date

import requests
import tqdm
from dict2xml import dict2xml
from PIL import Image

logger = logging.getLogger(__name__)


class TqdmLoggingHandler(logging.Handler):
    """
    Handles logging for tqdm
    """

    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.tqdm.write(msg)
            self.flush()
        except Exception:
            self.handleError(record)


logger.addHandler(TqdmLoggingHandler())
logger.propagate = False


class ChapterInfo(TypedDict):
    """Typehint for chapter info dictionary"""

    id: str
    series_id: str
    chapter: float
    volume: int
    title: str


class SeriesInfo(TypedDict):
    """Typehint for series info return"""

    id: str
    title: str
    description: str
    year: int
    author: str


class VolumeInfo(TypedDict):
    """Typehint for volume"""

    volume: str
    chapters: Dict


class BadChapterData(Exception):
    """Raised when data retreieved for data is bad"""


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


def is_mangadex_url(url: str) -> bool:
    """
    Determine if the url given is for MangaDex

    Arguments:
        url (str): the string to test

    Returns:
        (bool): true if the string is a valid MangaDex url, false otherwise
    """
    return bool(
        re.match(
            r"^(?:http(s)?:\/\/)?mangadex\.org\/?",
            url,
        )
        if is_url(url)
        else False
    )


def get_mangadex_resource(url: str) -> Tuple[str, str]:
    """
    Gets the resource and its type from a mangadex url

    Arguments:
        url (str): the url to get the needed information from

    Returns:
        (Tuple[str, str]): a tuple containing the type of resource and the UUID of the resource
        For example:
        ("title", "a96676e5-8ae2-425e-b549-7f15dd34a6d8")
    """
    mangadex_type = ""
    resource = ""

    search = re.search(
        r"^(?:http(s)?:\/\/)?mangadex\.org\/([\w]+)\/"
        r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\/?",
        url,
    )
    try:
        mangadex_type = search.group(2)
        resource = search.group(3)

    except AttributeError as err:
        raise ValueError("Could not get resource type or resource UUID!") from err

    return (mangadex_type, resource)


def get_mangadex_request(url: str) -> requests.Response:
    """
    Perform a request to the mangadex server with the appropiate rules in place (rate limiting etc)

    Arguments:
        url (str): the url to perform the request on

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

    sleep(0.5)
    return response


def get_mangadex_response(url: str) -> Dict:
    """
    Gets the response from get_mangadex_request but in the json format
    I wrote a lot of code relying on this before I moved it to the afformentioned function, and
    didn't want to update all the references

    Arguments:
        url (str): the url to perform the request to

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
        chapter (ChapterInfo): the chapter information (see mangadex_dl.chapter.get_chapter_info)
        series (SeriesInfo): the series information (see mangadex_dl.series.get_series_info)

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


def download_image(url: str, path: str, max_height: int = 2400):
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

    Raises:
        OSError: if the image has any trouble saving or downloading
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Attempt download 5 times
    for attempt in range(5):
        if attempt > 0:
            logger.warning(
                "Download for %s failed, retrying (attempt %i/5)", url, attempt
            )

        try:
            image = get_image_data(url, max_height)
            if image is None:
                continue

            image.save(path, quality=90)
            break
        except OSError:
            continue
    else:
        raise OSError("Failed to download and save image!")


def get_image_data(url: str, max_height: int) -> Image:
    """
    Get image data from URL in PIL.Image format

    Arguments:
        url (str): the url to get the image data from
        max_height (int): the maximum height of the image, downscaled if too tall

    Returns:
        (Pil.Image.Image): the PIL image
    """
    try:
        response = get_mangadex_request(url)
    except (requests.HTTPError, requests.Timeout):
        return None

    image = Image.open(io.BytesIO(response.content))
    image = image.convert("RGB")

    # Downscale if too big
    width, height = image.size
    if height > max_height:
        logger.info(
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
    Removes any character that is not a word, - (dash), _ (underscore), . (period) or space (  )
    from the name to make it useable for folder and file names
    """
    return re.sub(r"[^\w\-_\. ]", "_", name)


def get_chapter_directory(chapter_number: float, chapter_title: str) -> str:
    """
    Get the format of the path for the chapter images
    Removes any character that is not a word, - (dash), _ (underscore), . (period) or space (  )
    from the chapter title

    Arguments:
        chapter_number (float): the chapter number
        chapter_title (str): the title of the chapter

    Returns:
        (str): the folder structure for the outputed files. For example:
            chapter_number -> 2.0, chapter_title -> "bar"
            returns: "002 bar"

    Raises:
        TypeError: if the  given chapter number is not a number
    """
    if not isinstance(chapter_number, int) and not isinstance(chapter_number, float):
        raise TypeError("Given chapter number is NaN")

    # Remove non-friendly file characters
    chapter_title = make_name_safe(chapter_title)

    return (f"{chapter_number:05.1f}").rstrip("0").rstrip(".") + f" {chapter_title}"
