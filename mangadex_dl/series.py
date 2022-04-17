"""Functions related to MangaDex series"""
import logging
import os
import re
from typing import List, Dict

from requests import HTTPError, Timeout, RequestException
from PIL.Image import Image

import mangadex_dl
from mangadex_dl import chapter as md_chapter

logger = logging.getLogger(__name__)
logger.addHandler(mangadex_dl.TqdmLoggingHandler())
logger.propagate = False


def get_series_info(series_id: str) -> mangadex_dl.SeriesInfo:
    """
    Get the information for the mangadex series.

    Arguments:
        series_id (str): the UUID of the mangadex series

    Returns:
        (Dict): a dictionary containing all the relevent information of the series. For example:
            {"id": "a96676e5-8ae2-425e-b549-7f15dd34a6d8",
             "title": "Komi-san wa Komyushou Desu.",
             "description": "Komi-san is a beautiful and...", # truncated for readability
             "year": 2016,
             "author": "Oda Tomohito",
             "cover_art_url": "https://uploads.mangadex.org/covers/..."} # truncated for readability

    Raises:
        ValueError: if the response does not contain the required data
        requests.HTTPError: if the response fails
    """

    series_info = {"id": series_id}

    try:
        response = mangadex_dl.get_mangadex_response(
            f"https://api.mangadex.org/manga/{series_id}?includes[]=author&includes[]=cover_art"
        )
    except (HTTPError, Timeout) as err:
        raise RequestException from err

    data = response.get("data").get("attributes", {})
    relationships = response.get("data").get("relationships")

    if relationships is None:
        raise ValueError("Could not get needed information!")

    title_info = data.get("title", {})
    for title_lang in ["en", "ja-ro", "ja"]:
        series_title = title_info.get(title_lang)
        if series_title is not None:
            series_info["title"] = series_title
            break
    else:
        raise ValueError("Could not get title information!")

    series_info["description"] = data.get("description", {}).get("en", "")
    series_info["year"] = data.get("year", 1900)

    # Get series author
    for relationship in relationships:
        if relationship.get("type") == "author":
            series_info["author"] = relationship.get("attributes", {}).get(
                "name", "No Author"
            )
            break
    else:
        series_info["author"] = "No Author"

    for relationship in relationships:
        if relationship.get("type") == "cover_art":
            cover_art_file = relationship.get("attributes", {}).get("fileName")

            if cover_art_file is None:
                continue

            series_info[
                "cover_art_url"
            ] = f"https://uploads.mangadex.org/covers/{series_id}/{cover_art_file}.512.jpg"
            break
    else:
        series_info["cover_art_url"] = None

    return series_info


def get_volumes_from_series(series_id: str) -> mangadex_dl.VolumeInfo:
    """
    Returns the volumes found within the aggregate call of the mangadex api

    Arguments:
        series_id (str): the series UUID to get the volumes from

    Returns:
        (Dict): the dictionairy containing the volumes

    Raises:
        request.RequestException: if the response was unsuccessful
    """
    volumes = []

    try:
        response = mangadex_dl.get_mangadex_response(
            f"https://api.mangadex.org/manga/{series_id}/aggregate?translatedLanguage[]=en"
        )
    except (HTTPError, Timeout) as err:
        raise RequestException from err

    raw_volumes = response.get("volumes", {})

    for raw_volume in raw_volumes.values():
        if not all(key in raw_volume for key in ["volume", "chapters"]):
            raise ValueError("Could not get the required volume information")

        volumes.append(
            {
                "volume": raw_volume.get("volume"),
                "chapters": raw_volume.get("chapters", {}),
            }
        )

    # Loop over all the volumes in the manga
    return volumes


def get_chapter_ids_from_volumes(volumes: List[mangadex_dl.VolumeInfo]) -> List[str]:
    """
    Gets the series chapter ids from the series id

    Arguments:
        volumes (List[mangadex_dl.VolumeInfo]): the list of volumes to get chapter ids from

    Returns:
        (List[str]): the UUIDs of the series chapters

    Raises:
        requests.RequestException: if the request wasn't successful
    """
    chapter_ids = []

    for volume in volumes:
        # MangaDex for some reason gives a list when there is only one chapter in a volume
        chapters_raw = (
            volume.get("chapters")
            if not isinstance(volume.get("chapters"), list)
            else {"0": volume.get("chapters")[0]}
        )

        if chapters_raw is None:
            logger.warning(
                "Chapters not found for volume %s", volume.get("volume", "N/A")
            )
            continue

        chapters = chapters_raw.values()

        # Add chapters to list
        for chapter in chapters:
            chapter_id = chapter.get("id")
            if chapter_id is None:
                logger.warning(
                    "Chapter id could not be retrieved for volume %s",
                    volume.get("volume", "N/A"),
                )
                continue

            chapter_ids.append(chapter_id)

    return chapter_ids


def get_series_chapters(chapter_ids: List[str]) -> List[mangadex_dl.SeriesInfo]:
    """
    Gets all the chapters and their relevent information

    Arguments:
        series_id (str): the UUID of the mangadex series

    Returns:
        (List[SeriesInfo]): returns the list of chapters and their relevent information
            (see get_series_info)
    """
    chapter_list = []
    for chapter_id in chapter_ids:
        chapter_list.append(md_chapter.get_chapter_info(chapter_id))

    return chapter_list


def download_cover(
    series_info: mangadex_dl.SeriesInfo,
    output_directory: str,
    volume_number: int = None,
):
    """
    Downloads the cover to the series in the specified output directory

    Arguments:
        series_info (mangadex_dl.SeriesInfo): the series information
        output_directory (str): the base directory where series are downloaded to
        volume_number (int): the volume cover to download

    Rasies:
        KeyError: if one of the fields in series_info is not valid
        OSError: if the cover image could not be downloaded or saved
    """

    if not all(key in series_info for key in ["title", "cover_art_url", "id"]):
        raise KeyError(
            "One of the needed fields in the parsed dictionaries is not valid!"
        )

    series_id = series_info.get("id")
    cover_url = series_info.get("cover_art_url")

    if volume_number is not None:
        cover_art_volumes = get_cover_art_volumes(series_id)
        if str(volume_number) in cover_art_volumes:
            cover_url = (
                f"https://uploads.mangadex.org/covers/{series_id}"
                f"/{cover_art_volumes.get(str(volume_number))}.512.jpg"
            )

    series_title = re.sub(r"[^\w\-_\. ]", "_", series_info.get("title"))
    cover_path = os.path.join(output_directory, f"{series_title}/cover.jpg")

    try:
        mangadex_dl.download_image(cover_url, cover_path, 1024)
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
        response = mangadex_dl.get_mangadex_response(
            f"https://api.mangadex.org/cover?locales[]=ja&manga[]={series_id}&limit=50&offset={offset}"
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


def get_downloaded_chapter_images(series_directory: str) -> List[float]:
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
        if chapter_image.endswith(".jpg"):
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
    chapters: List[mangadex_dl.ChapterInfo],
    excluded_chapters: List[float] = (),
) -> Dict[str, Image]:
    """
    Get the required cover arts for the provided chapters

    Arguments:
        series_id (str): the series UUID the chapters originate from
        chapters (List[mangadex_dl.ChapterInfo]): the list of chapters
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
                cached_volume_images[volume_number] = mangadex_dl.get_image_data(
                    f"https://uploads.mangadex.org/covers/{series_id}/{file_name}.512.jpg",
                    512,
                )
            except ValueError:
                continue

    return cached_volume_images
