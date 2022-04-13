import os
import sys
import shutil
import json

import mangadex_dl
from mangadex_dl import Series, Chapter
from mangadex_dl import series as md_series
from mangadex_dl import chapter as md_chapter


class MangaDexDL:
    def __init__(self, cache_file_path: str, out_directory: str):
        self._cache_file_path = cache_file_path
        self._output_directory = out_directory

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
        with open(self._cache_file_path, "r+") as f:
            file_data = json.load(f)
            file_data.append(chapter_id)
            f.seek(0)
            json.dump(file_data, f, indent=4)

    def handle_url(self, url: str):
        if mangadex_dl.is_mangadex_url(url):
            self._handle_mangadex_url(url)
        else:
            print("Not a valid MangaDex URL")
            sys.exit(1)

    def handle_series_id(self, series_id: str):
        series_info = md_series.get_series_info(series_id)
        chapter_cache = md_series.get_chapter_cache(self._cache_file_path)
        series_chapters = md_series.get_chapters(series_id, chapter_cache)

        for chapter in series_chapters:
            file_directory = os.path.join(
                self._output_directory,
                md_chapter.get_chapter_directory(
                    series_info.get("title"),
                    chapter.get("chapter"),
                    chapter.get("title"),
                ),
            )

            md_chapter.download_chapter(file_directory, chapter, series_info)
            self._add_chapter_to_downloaded(chapter.get("id"))

            mangadex_dl.create_cbz(file_directory)
            mangadex_dl.create_comicinfo(file_directory, chapter, series_info)

            shutil.rmtree(file_directory)

    def handle_chapter_id(self, chapter_id: str):
        chapter = Chapter(chapter_id)
        chapter.download(self._output_directory)

    def get_series_from_id(self, series_id: str):
        return Series(series_id, self._cache_file_path)
