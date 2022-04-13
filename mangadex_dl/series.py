import json
from typing import List, Dict, Tuple

import mangadex_dl
from mangadex_dl import chapter as md_chapter


def get_chapter_cache(cache_file_path: str):
    try:
        with open(cache_file_path, "r", encoding="utf-8") as fin:
            return json.load(fin)
    except FileNotFoundError:
        return []


def get_series_info(series_id: str) -> Dict:
    print(f"Downloading info for series ({series_id})")

    series_info = {"id": series_id}

    response = mangadex_dl.get_mangadex_response(
        f"https://api.mangadex.org/manga/{series_id}?includes[]=author"
    )

    data = response.get("data").get("attributes")
    relationships = response.get("data").get("relationships")

    series_info["title"] = data.get("title", {}).get("en", "No Title")
    series_info["description"] = data.get("description", {}).get("en", "")
    series_info["year"] = data.get("year", 1900)

    for relationship in relationships:
        if relationship.get("type") == "author":
            series_info["author"] = relationship.get("attributes", {}).get(
                "name", "No Author"
            )
            break
    else:
        series_info["author"] = "No Author"

    return series_info


def get_chapters(series_id: str, excluded_chapters: Tuple = ()) -> List:
    # print(f"Getting chapters for series {self._title} ({self._id})")
    chapters = []

    response = mangadex_dl.get_mangadex_response(
        f"https://api.mangadex.org/manga/{series_id}/aggregate?translatedLanguage[]=en"
    )

    volumes = response.get("volumes")

    for volume in volumes.values():
        chapters_raw = (
            volume.get("chapters")
            if not isinstance(volume.get("chapters"), list)
            else {"0": volume.get("chapters")[0]}
        ).values()

        for chapter in chapters_raw:
            chapter_id = chapter.get("id")
            if chapter_id not in excluded_chapters:
                chapters.append(md_chapter.get_chapter_info(chapter_id))

    return chapters
