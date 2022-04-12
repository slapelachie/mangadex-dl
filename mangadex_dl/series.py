from typing import List

from mangadex_dl import utils


class Series:
    def __init__(self, id: str):
        self._id = id
        self._title = None
        self._description = None
        self._year = None
        self._author = None
        self._chapters = []

        self._get_info()
        print(f"Created new series {self._title} ({self._id})")

    def _get_info(self):
        print(f"Downloading info for series {self._title} ({self._id})")
        response = utils.get_mangadex_response(
            f"https://api.mangadex.org/manga/{self._id}?includes[]=author"
        )

        data = response.get("data").get("attributes")
        relationships = response.get("data").get("relationships")

        self._title = data.get("title").get("en")
        self._description = data.get("description").get("en")
        self._year = data.get("year")

        for relationship in relationships:
            if relationship.get("type") == "author":
                self._author = relationship.get("attributes").get("name")

    def _get_chapters(self):
        from mangadex_dl.chapter import Chapter
        from mangadex_dl.chapter import get_chapter_cache

        print(f"Getting chapters for series {self._title} ({self._id})")

        response = utils.get_mangadex_response(
            f"https://api.mangadex.org/manga/{self._id}/aggregate?translatedLanguage[]=en"
        )

        volumes = response.get("volumes")

        for volume in volumes.values():
            chapters = (
                volume.get("chapters")
                if not isinstance(volume.get("chapters"), list)
                else {"0": volume.get("chapters")[0]}
            ).values()

            for chapter in chapters:
                if chapter.get("id") not in get_chapter_cache():
                    self._chapters.append(Chapter(chapter.get("id"), series=self))

    def get_id(self) -> str:
        return self._id

    def get_title(self) -> str:
        return self._title

    def get_description(self) -> str:
        return self._description

    def get_year(self):
        return self._year

    def get_author(self):
        return self._author

    def get_chapters(self) -> List["Chapter"]:
        if len(self._chapters) == 0:
            self._get_chapters()

        return self._chapters
