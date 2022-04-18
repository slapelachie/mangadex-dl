"""Functions related to chapters"""
import os
import json
import logging
import re
from typing import List, Dict

import tqdm
from requests import HTTPError, Timeout, RequestException

import mangadex_dl

logger = logging.getLogger(__name__)
logger.addHandler(mangadex_dl.TqdmLoggingHandler())
logger.propagate = False


def get_chapter_info(chapter_id: str) -> mangadex_dl.ChapterInfo:
    """
    Gets the related info of the given chapter

    Arguments:
        chapter_id (str): the UUID of the mangadex chapter

    Returns:
        (Dict): a dictionary containing the relevent chapter information. For example:
            {"id": "56eecc6f-1a4e-464c-b6a4-a1cbdfdfd726",
             "series_id": "a96676e5-8ae2-425e-b549-7f15dd34a6d8",
             "chapter": 350.0,
             "volume": 0,
             "title": "New Phone"}

    Raises:
        requests.HTTPError: if the given URL did not return successfuly (status 200)
        KeyError: if the response doesn't contain the required information
    """
    chapter_info = {"id": chapter_id}

    try:
        response = mangadex_dl.get_mangadex_response(
            f"https://api.mangadex.org/chapter/{chapter_id}"
        )
    except (HTTPError, Timeout) as err:
        raise RequestException from err

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
        raise ValueError("Could not get series_id from chapter!")

    try:
        chapter_info["chapter"] = float(attributes.get("chapter", 0))
        volume = attributes.get("volume")
        chapter_info["volume"] = int(volume if volume is not None else 0)
    except ValueError as err:
        raise ValueError("Could not get chapter number or volume number") from err

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
        (List[str]): a list of the chapter image urls, empty if could not get images

    Raises:
        HTTPError: if the requested chapter id could not be found
    """
    chapter_urls = []

    try:
        response = mangadex_dl.get_mangadex_response(
            f"https://api.mangadex.org/at-home/server/{chapter_id}"
        )
    except (HTTPError, Timeout) as err:
        raise RequestException from err

    # Get the image path data
    chapter_image_data = response.get("chapter", {}).get("data")
    if chapter_image_data is None:
        raise mangadex_dl.BadChapterData("Could not find chapter URLs")

    # Create a url from the given data
    for chapter_image in chapter_image_data:
        base_url = response.get("baseUrl")
        chapter_hash = response.get("chapter", {}).get("hash")

        if base_url is None or chapter_hash is None:
            raise mangadex_dl.BadChapterData(
                f"Chapter {chapter_id} URL could not be retrieved"
            )

        chapter_urls.append(f"{base_url}/data/{chapter_hash}/{chapter_image}")

    return chapter_urls


def download_chapter(
    output_directory: str,
    chapter: mangadex_dl.ChapterInfo,
    series: mangadex_dl.SeriesInfo,
    progress_bars: bool = False,
):
    """
    Downloads all pages of a given chapter to the given output directory

    Arguments:
        output_directory (str): where to store the images
        chapter (mangadex_dl.ChapterInfo): the chapter information
            (see mangadex_dl.chapter.get_chapter_info)
        series (mangadex_dl.SeriesInfo): the series information
            (see mangadex_dl.series.get_series_info)

    Raises:
        KeyError: if one of the parsed dictionaries doesnt contain a required key
        OSError: if one of the chapter images has trouble saving
    """
    chapter_title = chapter.get("title")

    if not all(key in chapter for key in ["id", "title", "chapter"]):
        raise KeyError(
            "One of the needed fields in the parsed dictionaries is not valid!"
        )

    chapter_number = float(chapter.get("chapter"))

    logger.info(
        'Downloading "%s" chapter "%s %s"',
        series.get("title", "N/A"),
        chapter_number,
        chapter_title,
    )

    try:
        image_urls = get_chapter_image_urls(chapter.get("id"))
    except RequestException as err:
        raise RequestException from err

    # Download each page
    for i, url in enumerate(
        tqdm.tqdm(
            image_urls,
            ascii=True,
            desc=f"{chapter_number} {chapter_title}",
            disable=not progress_bars,
            position=0,
            leave=False,
        ),
        start=1,
    ):
        logger.info(
            'Downloading page %i of chapter "%s %s"', i, chapter_number, chapter_title
        )
        file_path = os.path.join(output_directory, f"{i:03}.jpg")

        try:
            mangadex_dl.download_image(url, file_path)
        except OSError as err:
            raise OSError from err


def get_chapter_cache(cache_file_path: str) -> Dict[str, List[str]]:
    """
    Get the chapter cache containing UUIDs of all previously downloaded chapters

    Arguments:
        cache_file_path (str): the path to the cache file

    Returns:
        (List[str]): the list of UUIDs in the cache
    """
    try:
        with open(cache_file_path, "r", encoding="utf-8") as fin:
            return json.load(fin)
    except FileNotFoundError:
        return {}


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
    chapter_title = mangadex_dl.make_name_safe(chapter_title)

    return (f"{chapter_number:05.1f}").rstrip("0").rstrip(".") + f" {chapter_title}"


def get_ids_not_excluded_chapters(
    grouped_ids: List[List[str]], excluded_chapters: List[str]
) -> List[str]:
    """
    Gets the first id from a group of ids iff none of the ids in the group are in the excluded
    chapters

    Arguments:
        grouped_ids (List[List[str]]): the grouped ids to process
        excluded_chapters (List[str]): the list of chapters to be excluded

    Returns:
        (List[str]): the first id iff match above statement
    """
    ids = []
    for chapter_ids in grouped_ids:
        if not any(uuid in chapter_ids for uuid in excluded_chapters):
            ids.append(chapter_ids[0])

    return ids


def get_ids_matched(grouped_ids: List[List[str]], to_match: List[str]) -> List[str]:
    """
    Get the list of ids iff the id is in the to_match list

    Arguments:
        grouped_ids (List[List[str]]): the grouped set of UUIDs
        to_match (List[str]): list of ids to match against

    Returns:
        (List[str]): the matched ids according to the above statement
    """
    return [
        uuid for chapter_ids in grouped_ids for uuid in chapter_ids if uuid in to_match
    ]
