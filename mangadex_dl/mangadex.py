"""The main handler for mangadex-dl"""
import os
import sys
import shutil
import json

import mangadex_dl
from mangadex_dl import series as md_series
from mangadex_dl import chapter as md_chapter


class MangaDexDL:
    """Handles all MangaDexDL related stuff"""

    def __init__(
        self, cache_file_path: str, out_directory: str, override: bool = False
    ):
        """
        Arguments:
            cache_file_path (str): the path for the file containing downloaded hashes is stored
            out_directory (str): where to store the downloaded content
        """
        self._cache_file_path = cache_file_path
        self._output_directory = out_directory
        self._override = override

        self._ensure_cache_file_exists()

    def _handle_mangadex_url(self, url: str):
        mangadex_type, resource_id = mangadex_dl.get_mangadex_resource(url)

        if mangadex_type == "title":
            self.handle_series_id(resource_id)
        elif mangadex_type == "chapter":
            self.handle_chapter_id(resource_id)

    def _ensure_cache_file_exists(self):
        if not os.path.exists(self._cache_file_path):
            os.makedirs(os.path.dirname(self._cache_file_path), exist_ok=True)
            with open(self._cache_file_path, "w+", encoding="utf-8") as fout:
                json.dump([], fout, indent=4)

    def _add_chapter_to_downloaded(self, chapter_id: str):
        with open(self._cache_file_path, "r+", encoding="utf-8") as raw_file:
            file_data = json.load(raw_file)
            file_data.append(chapter_id)
            raw_file.seek(0)
            json.dump(file_data, raw_file, indent=4)

    def _process_chapter(self, chapter_info, series_info):
        file_directory = os.path.join(
            self._output_directory,
            md_chapter.get_chapter_directory(
                series_info.get("title"),
                float(chapter_info.get("chapter")),
                chapter_info.get("title"),
            ),
        )

        md_chapter.download_chapter(file_directory, chapter_info, series_info)
        self._add_chapter_to_downloaded(chapter_info.get("id"))

        mangadex_dl.create_comicinfo(file_directory, chapter_info, series_info)
        mangadex_dl.create_cbz(file_directory)

        shutil.rmtree(file_directory)

    def handle_url(self, url: str):
        """
        Handle the given url

        Arguments:
            url (str): the url to handle
        """
        if mangadex_dl.is_mangadex_url(url):
            self._handle_mangadex_url(url)
        else:
            print("Not a valid MangaDex URL")
            sys.exit(1)

    def handle_series_id(self, series_id: str):
        """
        Handles a given series ID and starts the download process of the entire series

        Arguments:
            series_id (str): the UUID of the mangadex series
        """
        series_info = md_series.get_series_info(series_id)
        excluded_chapters = (
            md_chapter.get_chapter_cache(self._cache_file_path)
            if not self._override
            else []
        )
        series_chapters = md_series.get_series_chapters(
            series_id, excluded_chapters=excluded_chapters
        )

        # Process all chapters
        for chapter in series_chapters:
            self._process_chapter(chapter, series_info)

    def handle_chapter_id(self, chapter_id: str):
        """
        Handles a given chapter id and prepares to start downloading the chapter

        Arguments:
            chapter_id (str): the UUID of the mangadex chapter
        """
        excluded_chapters = (
            md_chapter.get_chapter_cache(self._cache_file_path)
            if not self._override
            else []
        )
        if chapter_id not in excluded_chapters:
            chapter_info = md_chapter.get_chapter_info(chapter_id)
            series_info = md_series.get_series_info(chapter_info.get("series_id"))

            self._process_chapter(chapter_info, series_info)
