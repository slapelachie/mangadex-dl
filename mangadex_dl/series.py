"""Functions related to MangaDex series"""
import logging
from typing import List, Dict, Tuple

from requests import HTTPError

import mangadex_dl
from mangadex_dl import chapter as md_chapter

logger = logging.getLogger(__name__)


def get_series_info(series_id: str) -> Dict:
    """
    Get the information for the mangadex series

    Arguments:
        series_id (str): the UUID of the mangadex series

    Returns:
        (Dict): a dictionary containing all the relevent information of the series
    """

    series_info = {"id": series_id}

    try:
        response = mangadex_dl.get_mangadex_response(
            f"https://api.mangadex.org/manga/{series_id}?includes[]=author"
        )
    except HTTPError as err:
        raise HTTPError from err

    data = response.get("data").get("attributes", {})
    relationships = response.get("data").get("relationships")

    if relationships is None:
        raise ValueError("Could not get needed information!")

    series_info["title"] = data.get("title", {}).get("en", "No Title")
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

    return series_info


def get_series_chapters(
    series_id: str, excluded_chapters: Tuple[str] = ()
) -> List[Dict]:
    """
    Gets all the chapters and their relevent information

    Arguments:
        series_id (str): the UUID of the mangadex series
        excluded_chapters (Tuple[str]): a list of chapters containing the uuids of chapters to be
                                        excluded

    Returns:
        (List[Dict]): returns the list of chapters and their relevent information
    """
    chapter_list = []

    response = mangadex_dl.get_mangadex_response(
        f"https://api.mangadex.org/manga/{series_id}/aggregate?translatedLanguage[]=en"
    )

    # Loop over all the volumes in the manga
    volumes = response.get("volumes")
    for volume in volumes.values():
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

            if chapter_id not in excluded_chapters:
                chapter_list.append(md_chapter.get_chapter_info(chapter_id))

    return chapter_list
