"""Functions related to chapters"""
import os
import json
import logging
from typing import List, Dict, Tuple

import tqdm
from requests import HTTPError, Timeout, RequestException

import mangadex_dlz
from mangadex_dlz.exceptions import ExternalChapterError

logger = logging.getLogger(__name__)
logger.addHandler(mangadex_dlz.TqdmLoggingHandler())
logger.propagate = False


def get_series_id_from_series_relationships(relationships: List[Dict]) -> str:
    """
    Gets the series id from the given relationships found in a mangadex chapter

    Arguments:
        relationships (List[Dict]): the list of relationship from a mangadex chapter

    Returns:
        (str): the mangadex series uuid
    """
    for relationship in relationships:
        if relationship.get("type") == "manga":
            return relationship["id"]

    return None


def get_chapter_mangadex(chapter_id: str) -> Tuple[Dict, Dict]:
    """
    Gets the raw chapter information from the mangadex api

    Arguments:
        chapter_id (str): the UUID of the mangadex chapter

    Returns:
        (List[Dict, Dict]): the attributes and relationships of the data

    Raises:
        requests.RequestException: if the given URL did not return successfuly (status 200)
    """
    try:
        response = mangadex_dlz.get_mangadex_response(
            f"https://api.mangadex.org/chapter/{chapter_id}"
        )
    except (HTTPError, Timeout) as err:
        raise RequestException from err

    data = response["data"]

    return (data["attributes"], data["relationships"])


def parse_chapter_info(
    chapter_id: str, series_id: str, attributes: Dict
) -> mangadex_dlz.ChapterInfo:
    """
    Parses the needed chapter information

    Arguments:
        chapter_id (str): the UUID of the mangadex chapter
        series_id (str): the UUID of the mangadex series from which the chapter originates
        attributes (Dict): the attributes returned from get_chapter_mangadex()

    Returns:
        (mangadex_dl.ChapterInfo): a dictionary containing the relevent chapter information.

    Raises:
        ValueError: if the chapter_number or volume number could not be extracted
    """

    if attributes.get("externalUrl"):
        raise ExternalChapterError("Chapter is externally sourced!")

    try:
        chapter_number = float(attributes["chapter"] or 0)
        volume_number = int(attributes["volume"] or 0)
    except ValueError as err:
        raise ValueError("Could not get chapter number or volume number") from err

    # Set the chapter title
    fallback_title = f"Chapter {chapter_number}"
    chapter_title = attributes["title"] or fallback_title

    logger.debug('Got chapter information for "%s %s"', chapter_number, chapter_title)

    return {
        "id": chapter_id,
        "series_id": series_id,
        "chapter": chapter_number,
        "volume": volume_number,
        "title": chapter_title,
    }


def get_chapter_info(chapter_id: str) -> mangadex_dlz.ChapterInfo:
    """
    Gets the related info of the given chapter

    Arguments:
        chapter_id (str): the UUID of the mangadex chapter

    Returns:
        (mangadex_dl.ChapterInfo): a dictionary containing the relevent chapter information.

    Raises:
        ValueError: if the series_id could not be extracted
    """
    attributes, relationships = get_chapter_mangadex(chapter_id)

    # Get the series ID
    series_id = get_series_id_from_series_relationships(relationships)
    if series_id is None:
        raise ValueError("Could not get series_id from chapter!")

    return parse_chapter_info(chapter_id, series_id, attributes)


def get_chapter_data(chapter_id: str) -> Tuple[str, str, List[str]]:
    """
    Gets the base url, hash and image urls from the mangadex at home server

    Arguments:
        chapter_id (str): the UUID for the mangadex chapter

    Returns:
        (Tuple[str, str, List[str]]): the base url, hash and image urls

    Raises:
        RequestExeption: if the requested chapter failed to be retrieved
    """
    try:
        response = mangadex_dlz.get_mangadex_response(
            f"https://api.mangadex.org/at-home/server/{chapter_id}"
        )
    except (HTTPError, Timeout) as err:
        raise RequestException from err

    chapter = response["chapter"]
    return (response["baseUrl"], chapter["hash"], chapter["data"])


def parse_chapter_image_urls(
    base_url: str, chapter_hash: str, chapter_images: List[str]
) -> List[str]:
    """
    Returns a list of constructed urls from the given arguments, see get_chapter_data()

    Arguments:
        base_url (str): the base url of the repository storing the chapter images
        chapter_hash (str): the hash of the chapter
        chapter_images (List[str]): paths of the chapter images

    Returns:
        (List[str]): list containing the constructed urls
    """
    return [
        f"{base_url}/data/{chapter_hash}/{chapter_image}"
        for chapter_image in chapter_images
    ]


def get_chapter_image_urls(chapter_id: str) -> List[str]:
    """
    Get the images (pages) for the given chapter

    Arguments:
        chapter_id (str): the UUID for the mangadex chapter

    Returns:
        (List[str]): a list of the chapter image urls, empty if could not get images
    """
    base_url, chapter_hash, chapter_data = get_chapter_data(chapter_id)
    return parse_chapter_image_urls(base_url, chapter_hash, chapter_data)


def download_chapter(
    output_directory: str,
    chapter: mangadex_dlz.ChapterInfo,
    series: mangadex_dlz.SeriesInfo,
    progress_bars: bool = False,
    enable_reporting: bool = False,
):
    """
    Downloads all pages of a given chapter to the given output directory

    Arguments:
        output_directory (str): where to store the images
        chapter (mangadex_dlz.ChapterInfo): the chapter information
            (see mangadex_dlz.chapter.get_chapter_info)
        series (mangadex_dlz.SeriesInfo): the series information
            (see mangadex_dlz.series.get_series_info)
        progress_bars (bool): if the progress bars should be enabled
        enable_reporting (bool): if reports on server health should be sent

    Raises:
        OSError: if one of the chapter images has trouble saving
    """
    chapter_title = chapter["title"]
    chapter_number = float(chapter["chapter"])

    logger.info(
        'Downloading "%s" chapter "%s %s"',
        series.get("title", "N/A"),
        chapter_number,
        chapter_title,
    )

    image_urls = get_chapter_image_urls(chapter["id"])

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
        file_path = os.path.join(output_directory, f"{i:03}.jpg")
        mangadex_dlz.download_image(url, file_path, enable_reporting=enable_reporting)


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
    chapter_title = mangadex_dlz.make_name_safe(chapter_title)

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
