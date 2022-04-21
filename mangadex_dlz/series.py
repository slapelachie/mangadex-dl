"""Functions related to MangaDex series"""
import logging
import os
import re
from typing import List, Dict, Tuple
from datetime import date

import tqdm
from requests import HTTPError, Timeout, RequestException
from PIL.Image import Image

import mangadex_dlz
from mangadex_dlz import chapter as md_chapter
from mangadex_dlz.exceptions import ExternalChapterError

logger = logging.getLogger(__name__)
logger.addHandler(mangadex_dlz.TqdmLoggingHandler())
logger.propagate = False


def get_series_mangadex(series_id: str) -> Tuple[Dict, Dict]:
    """
    Get's the series information from the mangadex api

    Arguments:
        series_id (str): the series uuid of the series to be downloaded

    Returns:
        (Tuple[Dict, Dict]): a tuple containing the attributes and relationships of the series

    Raises:
        requests.HTTPError: if the response fails
    """
    try:
        response = mangadex_dlz.get_mangadex_response(
            f"https://api.mangadex.org/manga/{series_id}?includes[]=author&includes[]=cover_art"
        )
    except (HTTPError, Timeout) as err:
        raise RequestException from err

    data = response["data"]

    return (data["attributes"], data["relationships"])


def get_series_title(title_info: Dict[str, str]) -> str:
    """
    Gets the series title from the title information retrieved from the mangadex series response

    Arguments:
        title_info (Dict[str, str]): the title info (see get_series_info())

    Returns:
        (str): the appropriate title
        (None): if the title could not be found
    """
    for title_lang in ["en", "ja-ro", "ja"]:
        series_title = title_info.get(title_lang)
        if series_title is not None:
            return series_title

    return None


def get_series_author(relationships: List[Dict]) -> str:
    """
    Get the series author from the relationships given by mangadex series

    Arguments:
        relationships (List[Dict]): the relationships (see get_series_info())

    Returns:
        (str): the name of the author, returns "No Author" if none was found
    """
    for relationship in relationships:
        if relationship.get("type") == "author":
            return relationship.get("attributes", {}).get("name") or "No Author"

    return "No Author"


def get_series_cover_art_url(series_id: str, relationships: List[Dict]) -> str:
    """
    Get the series cover art url from the relationships given by the series api call

    Arguments:
        series_id (str): the series id of the series from which the cover originates
        relationships (List[Dict]): the relationships (see get_series_info())

    Returns:
        (str): the url to the cover
        (None): if no cover url was found
    """
    for relationship in relationships:
        if relationship.get("type") == "cover_art":
            cover_art_file = relationship.get("attributes", {}).get("fileName")
            if cover_art_file is None:
                continue

            return f"https://uploads.mangadex.org/covers/{series_id}/{cover_art_file}.512.jpg"

    return None


def parse_series_info(
    series_id: str, attributes: Dict, relationships: Dict
) -> mangadex_dlz.SeriesInfo:
    """
    Parses the information from the given attributes and relationships

    Arguments:
        series_id (str): the UUID of the mangadex series
        attributes (Dict): the attributes from the series
        relationships (Dict): the relationships of the series

    Returns:
        (mangadex_dl.exceptions.SeriesInfo): a dictionary containing all
            the relevent information of the series

    Raises:
        ValueError: if the response does not contain the required data
    """
    title_info = attributes.get("title", {})
    series_title = get_series_title(title_info)
    if series_title is None:
        raise ValueError("Could not get title information!")

    return {
        "id": series_id,
        "title": series_title,
        "description": attributes.get("description", {}).get("en", ""),
        "year": int(attributes.get("year") or date.today().year),
        "author": get_series_author(relationships),
        "cover_art_url": get_series_cover_art_url(series_id, relationships),
    }


def get_series_info(series_id: str) -> mangadex_dlz.SeriesInfo:
    """
    Get the information for the mangadex series.

    Arguments:
        series_id (str): the UUID of the mangadex series

    Returns:
        (mangadex_dl.exceptions.SeriesInfo): a dictionary containing all
            the relevent information of the series
    """
    attributes, relationships = get_series_mangadex(series_id)
    return parse_series_info(series_id, attributes, relationships)


def process_mangadex_volumes(mangadex_volumes: Dict) -> Dict[str, Dict[str, List[str]]]:
    """
    Converts the mangadex response volume to a more useable dictionary

    Arguments:
        mangadex_volumes (Dict): the volume part of the response from the mangadex aggregate query
            (see get_volumes_from_series)

    Returns:
        (Dict[str, Dict[str, List[str]]])

    Raises:
        KeyError: if the mangadex_volume does not have the required keys
    """
    volumes = {}
    for mangadex_volume in mangadex_volumes.values():
        volume_number = mangadex_volume["volume"]
        for mangadex_chapter in mangadex_volume["chapters"].values():
            chapter_number = mangadex_chapter["chapter"]
            volumes.setdefault(volume_number, {})[chapter_number] = [
                mangadex_chapter["id"]
            ]

            other_chapters = mangadex_chapter.get("others", [])
            volumes.get(volume_number).get(chapter_number).extend(other_chapters)

    return volumes


def get_volumes_from_series(series_id: str) -> Dict[str, Dict[str, List[str]]]:
    """
    Returns the volumes found within the aggregate call of the mangadex api

    Arguments:
        series_id (str): the series UUID to get the volumes from

    Returns:
        (Dict): the dictionairy containing the volumes

    Raises:
        request.RequestException: if the response was unsuccessful
    """
    try:
        response = mangadex_dlz.get_mangadex_response(
            f"https://api.mangadex.org/manga/{series_id}/aggregate?translatedLanguage[]=en"
        )
    except (HTTPError, Timeout) as err:
        raise RequestException from err

    raw_volumes = response.get("volumes", {})
    try:
        return process_mangadex_volumes(raw_volumes)
    except KeyError as err:
        raise err


def get_grouped_chapter_ids_from_volumes(
    volumes: Dict[str, Dict[str, List[str]]]
) -> List[List[str]]:
    """
    Gets the series chapter ids from the series id

    Arguments:
        volumes (Dict[str, Dict[str, str]]): the list of volumes to get chapter ids from, gets the
            first chapter id if there are multiple for a chapter

    Returns:
        (List[List[str]]): the UUIDs of the series chapters
    """
    return [uuids for chapters in volumes.values() for uuids in chapters.values()]


def get_series_chapters(
    chapter_ids: List[str], progress_bars: bool = False
) -> List[mangadex_dlz.SeriesInfo]:
    """
    Gets all the chapters and their relevent information

    Arguments:
        series_id (str): the UUID of the mangadex series
        progress_bars (bool): whether to enable progress bars

    Returns:
        (List[SeriesInfo]): returns the list of chapters and their relevent information
            (see get_series_info)
    """
    chapter_list = []
    for chapter_id in tqdm.tqdm(
        chapter_ids,
        ascii=True,
        desc="Chapter Info",
        disable=not progress_bars,
        position=1,
        leave=False,
    ):
        try:
            chapter_list.append(md_chapter.get_chapter_info(chapter_id))
        except ExternalChapterError:
            logger.info("Chapter is from an external source, skipping...")
            continue

    return chapter_list


def get_cover_url_volume(volume_number: int, series_id: str) -> str:
    """
    Get the volume cover for a specific volume number

    Arguments:
        volume_number (int): the volume number to fetch the cover for
        series_id (str): the series id of the specific volume

    Returns:
        (str): the url to the volume cover
    """
    cover_art_volumes = get_cover_art_volumes(series_id)
    if str(volume_number) in cover_art_volumes:
        return (
            f"https://uploads.mangadex.org/covers/{series_id}"
            f"/{cover_art_volumes.get(str(volume_number))}.512.jpg"
        )

    return None


def download_cover(
    series_info: mangadex_dlz.SeriesInfo,
    output_directory: str,
    volume_number: int = None,
):
    """
    Downloads the cover to the series in the specified output directory

    Arguments:
        series_info (mangadex_dlz.SeriesInfo): the series information
        output_directory (str): the base directory where series are downloaded to
        volume_number (int): the volume cover to download
        enable_reporting (bool): if reports on server health should be sent

    Rasies:
        KeyError: if one of the fields in series_info is not valid
        OSError: if the cover image could not be downloaded or saved
    """
    series_id = series_info["id"]
    cover_url = series_info["cover_art_url"]

    if volume_number is not None:
        cover_url = get_cover_url_volume(volume_number, series_id) or cover_url

    series_title = mangadex_dlz.make_name_safe(series_info["title"])
    cover_path = os.path.join(output_directory, f"{series_title}/cover.jpg")

    try:
        mangadex_dlz.download_image(cover_url, cover_path, 1024)
    except OSError as err:
        raise OSError("Failed to download and save cover image!") from err


def get_cover_art_volumes(series_id: str, offset: int = 0) -> Dict[str, str]:
    """
    Get the cover art urls for the series

    Arguments:
        series_id (str): the series UUID to download covers from

    Returns:
        (Dict[str, str]): a dictionary containing the covers. For example:
            {"2": "26130c5c-eb15-4ff6-acb9-27532d5ee5c5.jpg",
             "3": "1a9286d5-55d9-4033-b73f-3948e3b27eeb.jpg"}

    Raises:
        requests.RequestException: if the list of chapters cannot be downloaded
    """
    cover_art_volumes = {}

    try:
        response = mangadex_dlz.get_mangadex_response(
            f"https://api.mangadex.org/cover?locales[]=ja&manga[]={series_id}"
            f"&limit=50&offset={offset}"
        )
    except (HTTPError, Timeout) as err:
        raise RequestException from err

    # Get all avaliable covers
    total_covers = response.get("total", 0)
    if total_covers > (offset + 50):
        cover_art_volumes = cover_art_volumes | get_cover_art_volumes(
            series_id, (offset + 50)
        )

    data = response.get("data")
    if data is None:
        raise ValueError(f"Could not get volume images for {series_id}")

    for volume in data:
        if volume.get("type") != "cover_art":
            continue

        volume_attributes = volume.get("attributes")
        if volume_attributes is None:
            raise ValueError(f"Could not get volume images for {series_id}")

        if not all(key in volume_attributes for key in ["volume", "fileName"]):
            raise ValueError(f"Could not get volume images for {series_id}")

        cover_art_volumes[volume_attributes.get("volume")] = volume_attributes.get(
            "fileName"
        )

    return cover_art_volumes


def get_downloaded_chapter_content(
    series_directory: str, extension: str
) -> List[float]:
    """
    Gets a list of chapter numbers already downloaded in the series directory

    Arguments:
        series_directory (str): the series directory to check for the images

    Returns:
        (List[float]): a list of all the chapter numbers
    """
    downloaded_chapters = []
    directory_images = []

    if os.path.exists(series_directory):
        directory_images = os.listdir(
            series_directory,
        )
    else:
        return []

    for chapter_image in directory_images:
        if chapter_image.endswith(f".{extension}"):
            search = re.search(
                r"([0-9]{3,}(?:.[0-9]{1,})?)\ ([\w\-_\. ]+)", chapter_image
            )
            chapter_number = None
            try:
                chapter_number = search.group(1)
            except AttributeError:
                continue

            if chapter_number is None:
                continue

            chapter_number = float(chapter_number)

            downloaded_chapters.append(chapter_number)

    return downloaded_chapters


def get_needed_volume_images(
    series_id: str,
    chapters: List[mangadex_dlz.ChapterInfo],
    excluded_chapters: List[float] = (),
) -> Dict[str, Image]:
    """
    Get the required cover arts for the provided chapters

    Arguments:
        series_id (str): the series UUID the chapters originate from
        chapters (List[mangadex_dlz.ChapterInfo]): the list of chapters
        excluded_chapters (List[float]): list of chapter numbers to not search for

    Returns:
        (Dict[str, PIL.Image.Image]): the dictionary containing all the volume chapter image data

    Raises:
        KeyError: if one of the chapters do not have the correct format
    """
    cached_volume_images = {}

    cover_art_volumes = get_cover_art_volumes(series_id)

    for chapter in chapters:
        if not all(key in chapter for key in ["volume", "chapter"]):
            raise KeyError(
                "Volume or Chapter key in one of the parsed chapters is not valid!"
            )

        if chapter.get("chapter") in excluded_chapters:
            continue

        volume_number = chapter.get("volume")
        if volume_number is None:
            continue

        volume_number = str(volume_number)

        if volume_number not in cover_art_volumes:
            continue

        file_name = cover_art_volumes.get(volume_number)
        if file_name is None:
            continue

        if volume_number not in cached_volume_images:
            try:
                cached_volume_images[volume_number] = mangadex_dlz.get_image_data(
                    f"https://uploads.mangadex.org/covers/{series_id}/{file_name}.512.jpg",
                    512,
                    enable_reporting=False,
                )
            except ValueError:
                continue

    return cached_volume_images
