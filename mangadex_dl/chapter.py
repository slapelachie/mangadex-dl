"""Functions related to chapters"""
import re
import os
import io
import json
import logging
from math import floor
from typing import Dict, List

from requests import HTTPError
from PIL import Image

import mangadex_dl

logger = logging.getLogger(__name__)


def get_chapter_info(chapter_id: str) -> Dict:
    """
    Gets the related info of the given chapter

    Arguments:
        chapter_id (str): the UUID of the mangadex chapter

    Returns:
        (Dict): a dictionary containing the relevent chapter information
    """
    chapter_info = {"id": chapter_id}

    try:
        response = mangadex_dl.get_mangadex_response(
            f"https://api.mangadex.org/chapter/{chapter_id}"
        )
    except HTTPError as err:
        raise HTTPError from err

    data = response.get("data", {})
    attributes = data.get("attributes")

    if attributes is None:
        raise ValueError("Could not get needed information!")

    # Get the series ID
    for relationship in data.get("relationships"):
        if relationship.get("type") == "manga":
            series_id = relationship.get("id", None)
            if series_id is None:
                continue

            chapter_info["series_id"] = series_id
            break
    else:
        raise KeyError("Could not get series_id from chapter!")

    chapter_info["chapter"] = attributes.get("chapter", 0)
    chapter_info["volume"] = attributes.get("volume", 0)

    # Set the chapter title
    fallback_title = f"Chapter {chapter_info['chapter']}"
    chapter_title = attributes.get("title", fallback_title)
    chapter_info["title"] = chapter_title or fallback_title

    logger.info('Got info for "%s %s"', chapter_info["chapter"], chapter_info["title"])

    return chapter_info


def get_chapter_image_urls(chapter_id: str) -> List[str]:
    """
    Get the images (pages) for the given chapter

    Arguments:
        chapter_id (str): the UUID for the mangadex chapter

    Returns:
        (List[str]): a list of the chapter image urls
    """
    chapter_urls = []

    response = mangadex_dl.get_mangadex_response(
        f"https://api.mangadex.org/at-home/server/{chapter_id}"
    )

    # Get the image path data
    chapter_image_data = response.get("chapter", {}).get("data")
    if chapter_image_data is None:
        logger.warning("Could not find chapter URLs")
        return []

    # Create a url from the given data
    for chapter_image in chapter_image_data:
        base_url = response.get("baseUrl")
        chapter_hash = response.get("chapter", {}).get("hash")

        if base_url is None or chapter_hash is None:
            logger.warning("Chapter %s URL could not be retrieved", chapter_id)
            continue

        chapter_urls.append(f"{base_url}/data/{chapter_hash}/{chapter_image}")

    return chapter_urls


def get_chapter_directory(
    series_title: str, chapter_number: float, chapter_title: str
) -> str:
    """
    Get the format of the path for the chapter images
    Removes any character that is not a word, - (dash), _ (underscore), . (period) or space (  )
    from the series title and chapter title

    Arguments:
        series_title (str): the title of the series
        chapter_number (float): the chapter number
        chapter_title (str): the title of the chapter

    Returns:
        (str): the folder structure for the outputed files
    """
    if not isinstance(chapter_number, float):
        raise TypeError()

    # Remove non-friendly file characters
    chapter_title = re.sub(r"[^\w\-_\. ]", "_", chapter_title)
    series_title = re.sub(r"[^\w\-_\. ]", "_", series_title)

    return (f"{series_title}/{chapter_number:05.1f}").rstrip("0").rstrip(
        "."
    ) + f" {chapter_title}"


def download_chapter_image(url: str, path: str):
    """
    Download the image from the given url to the specified path
    Image is converted to RGB, downscaled to a height of 2400 pixels if it exceeds this height,
    and then saved as a to the given path

    The download and saving is attempted 5 times before aborting, this is because there was a time
    where pillow complained about the image being truncated, and on the next attempt it was fine

    Arguments:
        url (str): the url of the mangadex chapter image (page)
        path (str): the output destination of the downloaded image
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Attempt download 5 times
    for attempt in range(5):
        if attempt > 0:
            logger.warning(
                "Download for %s failed, retrying (attempt %i/5)", url, attempt
            )

        try:
            response = mangadex_dl.get_mangadex_request(url)
        except HTTPError:
            continue

        try:
            image = Image.open(io.BytesIO(response.content))
            image = image.convert("RGB")

            # Downscale if too big
            width, height = image.size
            new_height = 2400
            if height > new_height:
                logger.info(
                    "Image height from %s is greater than 2400 pixels, downscaling..."
                )
                ratio = width / height
                new_width = floor(ratio * new_height)
                image = image.resize((new_width, new_height), Image.BICUBIC)

            image.save(path, quality=90)
            break
        except OSError:
            continue
    else:
        raise OSError("Failed to download and save image!")


def download_chapter(output_directory: str, chapter: Dict, series: Dict):
    """
    Downloads all pages of a given chapter to the given output directory

    Arguments:
        output_directory (str): where to store the images
        chapter (Dict): the chapter information (see mangadex_dl.chapter.get_chapter_info)
        series (Dict): the series information (see mangadex_dl.series.get_series_info)
    """
    chapter_title = chapter.get("title")

    if not all(key in chapter for key in ["id", "title", "chapter"]):
        raise KeyError(
            "One of the needed fields in the parsed dictionaries is not valid!"
            "Could not download the chapter."
        )

    chapter_number = float(chapter.get("chapter"))

    logger.info(
        'Downloading "%s" chapter "%s %s"',
        series.get("title", "N/A"),
        chapter_number,
        chapter_title,
    )

    image_urls = get_chapter_image_urls(chapter.get("id"))

    # Download each page
    for i, url in enumerate(image_urls, start=1):
        logger.info(
            'Downloading page %i of chapter "%s %s"', i, chapter_number, chapter_title
        )
        file_path = os.path.join(output_directory, f"{i:03}.jpg")

        try:
            download_chapter_image(url, file_path)
        except OSError as err:
            raise OSError from err


def get_chapter_cache(cache_file_path: str):
    """
    Get the chapter cache containing UUIDs of all previously downloaded chapters
    """
    try:
        with open(cache_file_path, "r", encoding="utf-8") as fin:
            return json.load(fin)
    except FileNotFoundError:
        return []
