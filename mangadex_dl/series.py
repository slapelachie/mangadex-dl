"""Functions related to MangaDex series"""
from typing import List, Dict, Tuple

import mangadex_dl
from mangadex_dl import chapter as md_chapter


def get_series_info(series_id: str) -> Dict:
    """
    Get the information for the mangadex series

    Arguments:
        series_id (str): the UUID of the mangadex series

    Returns:
        (Dict): a dictionary containing all the relevent information of the series
    """

    series_info = {"id": series_id}

    response = mangadex_dl.get_mangadex_response(
        f"https://api.mangadex.org/manga/{series_id}?includes[]=author"
    )

    data = response.get("data").get("attributes")
    relationships = response.get("data").get("relationships")

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
    chapters = []

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
        ).values()

        # Add chapters to list
        for chapter in chapters_raw:
            chapter_id = chapter.get("id")
            if chapter_id not in excluded_chapters:
                chapters.append(md_chapter.get_chapter_info(chapter_id))

    return chapters
