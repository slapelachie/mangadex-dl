"""The main handler for mangadex-dl"""
import os
import sys
import shutil
import json
import logging
import re
from typing import List, Tuple, Dict

import tqdm
from requests import RequestException

import mangadex_dlz
from mangadex_dlz import ComicInfoError, FailedImageError
from mangadex_dlz import series as md_series
from mangadex_dlz import chapter as md_chapter

logger = logging.getLogger(__name__)
logger.addHandler(mangadex_dlz.TqdmLoggingHandler())
logger.propagate = False


class MangaDexDL:
    """Handles all MangaDexDL related stuff"""

    def __init__(
        self,
        cache_file_path: str,
        out_directory: str,
        override: bool = False,
        download_cover: bool = False,
        progress_bars: bool = False,
        reporting: bool = False,
    ):
        """
        Arguments:
            cache_file_path (str): the path for the file containing downloaded hashes is stored
            out_directory (str): where to store the downloaded content
        """
        self._cache_file_path = cache_file_path
        self._output_directory = out_directory
        self._override = override
        self._download_cover = download_cover
        self._progress_bars = progress_bars
        self._reporting = reporting

        try:
            self._ensure_cache_file_exists()
        except OSError as err:
            logger.exception(err)
            sys.exit(1)

    def _download_from_mangadex_url(self, url: str):
        try:
            mangadex_type, resource_id = get_mangadex_resource(url)
        except ValueError as err:
            raise ValueError from err

        logger.debug("Supplied URL is of type %s", mangadex_type)
        logger.debug("Resource ID is %s", resource_id)

        if mangadex_type == "title":
            self.download_series_from_id(resource_id)
        elif mangadex_type == "chapter":
            self.download_chapter_from_id(resource_id)

    def _ensure_cache_file_exists(self):
        if not os.path.exists(self._cache_file_path):
            logger.debug("%s does not exist, creating it...", self._cache_file_path)
            os.makedirs(os.path.dirname(self._cache_file_path), exist_ok=True)
            try:
                with open(self._cache_file_path, "w+", encoding="utf-8") as fout:
                    json.dump({}, fout, indent=4)
            except OSError as err:
                raise OSError(
                    f"Could not create required cache file at {self._cache_file_path}"
                ) from err

    def _add_chapter_to_downloaded(self, series_id: str, chapter_id: str):
        for _ in range(2):
            try:
                with open(self._cache_file_path, "r+", encoding="utf-8") as raw_file:
                    file_data = json.load(raw_file)
                    file_data.setdefault(series_id, []).append(chapter_id)
                    raw_file.seek(0)
                    json.dump(file_data, raw_file, indent=4)
                    break
            except FileNotFoundError:
                try:
                    self._ensure_cache_file_exists()
                except OSError:
                    continue
        else:
            raise FileNotFoundError(
                f"Could not find required cache file at {self._cache_file_path}"
            )

    def _process_chapter(
        self,
        chapter_info: mangadex_dlz.ChapterInfo,
        series_info: mangadex_dlz.SeriesInfo,
    ):
        if "title" not in series_info or not all(
            key in chapter_info for key in ["chapter", "title", "id"]
        ):
            raise KeyError(
                "Needed information from chapter or series not present! Exiting..."
            )

        series_title = series_info.get("title")
        chapter_number = chapter_info.get("chapter")
        chapter_title = chapter_info.get("title")

        logger.debug(
            'Processing "%s" chapter "%s %s"',
            series_title,
            chapter_number,
            chapter_title,
        )

        chapter_directory = os.path.join(
            self._output_directory,
            os.path.join(
                mangadex_dlz.make_name_safe(series_title),
                md_chapter.get_chapter_directory(float(chapter_number), chapter_title),
            ),
        )

        try:
            md_chapter.download_chapter(
                chapter_directory,
                chapter_info,
                series_info,
                progress_bars=self._progress_bars,
                enable_reporting=self._reporting,
            )
        except (KeyError, OSError) as err:
            raise FailedImageError("Failed to download image!") from err

        if not self._override:
            try:
                self._add_chapter_to_downloaded(
                    series_info.get("id"), chapter_info.get("id")
                )
            except OSError as err:
                raise err

        logger.debug(
            "Creating %s.cbz",
            chapter_directory,
        )

        try:
            mangadex_dlz.create_comicinfo(chapter_directory, chapter_info, series_info)
        except (KeyError, OSError) as err:
            shutil.rmtree(chapter_directory)
            raise ComicInfoError("Failed to create ComicInfo.xml!") from err

        try:
            mangadex_dlz.create_cbz(chapter_directory)
        except (NotADirectoryError, OSError) as err:
            shutil.rmtree(chapter_directory)
            raise OSError("Failed to create archive!") from err

        shutil.rmtree(chapter_directory)

    def _get_chapters_from_cache(self):
        chapters = []

        if self._override:
            return []

        chapter_cache = md_chapter.get_chapter_cache(self._cache_file_path)
        for series in chapter_cache:
            chapters.extend(chapter_cache[series])

        return chapters

    def _download_chapter_covers(
        self,
        series_info: mangadex_dlz.SeriesInfo,
        chapters: List[mangadex_dlz.ChapterInfo],
    ):
        series_title = series_info.get("title")
        downloaded_chapter_images = md_series.get_downloaded_chapter_content(
            os.path.join(
                self._output_directory,
                mangadex_dlz.make_name_safe(series_info.get("title")),
            ),
            "jpg",
        )

        logger.debug("Getting volume images for %s", series_title)
        volume_images = md_series.get_needed_volume_images(
            series_info.get("id"),
            chapters,
            excluded_chapters=downloaded_chapter_images,
        )

        for chapter in tqdm.tqdm(
            chapters,
            ascii=True,
            desc="covers",
            disable=not self._progress_bars,
            position=1,
            leave=False,
        ):
            if not all(key in chapter for key in ["chapter", "volume", "title"]):
                raise KeyError(
                    "One of the needed fields in the parsed chapters is not valid!"
                )

            chapter_directory = os.path.join(
                self._output_directory,
                os.path.join(
                    mangadex_dlz.make_name_safe(series_title),
                    md_chapter.get_chapter_directory(
                        chapter.get("chapter"), chapter.get("title")
                    ),
                ),
            )

            volume_number = str(chapter.get("volume") or "")
            if volume_number != "":
                volume_image = volume_images.get(volume_number)
                if volume_image is not None:
                    volume_image.save(f"{chapter_directory}.jpg")

    def _get_pending_chapters_from_volumes(
        self, volumes: Dict[str, Dict[str, List[str]]]
    ):
        excluded_chapters = self._get_chapters_from_cache()
        grouped_ids = md_series.get_grouped_chapter_ids_from_volumes(volumes)
        chapter_ids = md_chapter.get_ids_not_excluded_chapters(
            grouped_ids, excluded_chapters
        )
        chapters = md_series.get_series_chapters(chapter_ids)

        return sorted(chapters, key=lambda d: d.get("chapter"))

    def _download_series_cover(
        self,
        series_info: mangadex_dlz.SeriesInfo,
        volumes: List[mangadex_dlz.VolumeInfo],
    ):
        if "title" not in series_info:
            logger.error("Could not get title from the parsed series info")

        volume_numbers = []
        for raw_volume_number in volumes:
            try:
                volume_number = int(raw_volume_number)
            except ValueError:
                volume_number = 0

            volume_numbers.append(volume_number)

        try:
            md_series.download_cover(
                series_info,
                self._output_directory,
                volume_number=max(volume_numbers),
            )
        except (KeyError, OSError) as err:
            logger.exception(err)
        else:
            logger.info("Downloaded cover for %s", series_info.get("title"))

    def download(self, url: str):
        """
        Handle the given url

        Arguments:
            url (str): the url to handle
        """
        if is_mangadex_url(url):
            self._download_from_mangadex_url(url)
        else:
            logger.critical("Not a valid MangaDex URL")
            sys.exit(1)

    def download_series_from_id(self, series_id: str):
        """
        Handles a given series ID and starts the download process of the entire series

        Arguments:
            series_id (str): the UUID of the mangadex series
        """
        logger.debug("Handling series with ID: %s", series_id)

        try:
            series_info = md_series.get_series_info(series_id)
        except (ValueError, RequestException) as err:
            logger.exception(err)
            sys.exit(1)

        series_title = series_info.get("title")
        logger.info("Got series information for %s", series_title)

        series_directory = os.path.join(
            self._output_directory, mangadex_dlz.make_name_safe(series_title)
        )
        os.makedirs(series_directory, exist_ok=True)

        try:
            series_volumes = md_series.get_volumes_from_series(series_id)
        except (RequestException, ValueError) as err:
            logger.exception(err)
            sys.exit(1)

        if self._download_cover:
            logger.info("Downloading cover for %s...", series_title)
            self._download_series_cover(series_info, series_volumes)

        logger.debug("Getting chapters for %s", series_title)
        chapters = self._get_pending_chapters_from_volumes(series_volumes)

        # Process all chapters
        for chapter in tqdm.tqdm(
            chapters,
            ascii=True,
            desc=f"{series_title}",
            disable=not self._progress_bars,
            position=1,
            leave=False,
        ):
            try:
                self._process_chapter(chapter, series_info)
            except (KeyError, FailedImageError, OSError, ComicInfoError) as err:
                logger.exception(err)
                sys.exit(1)

    def download_chapter_from_id(self, chapter_id: str):
        """
        Handles a given chapter id and prepares to start downloading the chapter

        Arguments:
            chapter_id (str): the UUID of the mangadex chapter
        """
        logger.debug("Handling chapter with ID: %s", chapter_id)
        try:
            chapter_info = md_chapter.get_chapter_info(chapter_id)
            series_info = md_series.get_series_info(chapter_info.get("series_id"))
        except (RequestException, ValueError, KeyError) as err:
            logger.exception(err)
            sys.exit(1)

        excluded_chapters = self._get_chapters_from_cache()
        if chapter_id not in excluded_chapters:
            try:
                self._process_chapter(chapter_info, series_info)
            except (KeyError, FailedImageError, OSError, ComicInfoError) as err:
                logger.exception(err)
                sys.exit(1)

    def download_covers(self, url: str):
        """
        Downloads the chapter covers for each chapter from the given url

        Arguments:
            url (str): the url of the chapter or series to download the chapters for
        """
        if not is_mangadex_url(url):
            logger.critical("Not a valid MangaDex URL")
            sys.exit(1)

        try:
            mangadex_type, resource_id = get_mangadex_resource(url)
        except ValueError as err:
            raise ValueError from err

        logger.debug("Supplied URL is of type %s", mangadex_type)
        logger.debug("Resource ID is %s", resource_id)

        if mangadex_type == "title":
            try:
                series_info = md_series.get_series_info(resource_id)
                series_volumes = md_series.get_volumes_from_series(resource_id)
            except (ValueError, RequestException) as err:
                logger.exception(err)
                sys.exit(1)

            grouped_chapter_ids = md_series.get_grouped_chapter_ids_from_volumes(
                series_volumes
            )
            pending_chapter_ids = md_chapter.get_ids_matched(
                grouped_chapter_ids, self._get_chapters_from_cache()
            )
            chapters = md_series.get_series_chapters(pending_chapter_ids)
        elif mangadex_type == "chapter":
            try:
                chapter_info = md_chapter.get_chapter_info(resource_id)
                series_info = md_series.get_series_info(chapter_info.get("series_id"))
            except (RequestException, ValueError, KeyError) as err:
                logger.exception(err)
                sys.exit(1)

            chapters = [chapter_info]
        else:
            logger.critical("MangaDex resource type is unhandled!")
            sys.exit(1)

        series_directory = os.path.join(
            self._output_directory,
            mangadex_dlz.make_name_safe(series_info.get("title")),
        )

        os.makedirs(series_directory, exist_ok=True)

        logger.info("Downloading chapter covers for %s...", series_info.get("title"))
        self._download_chapter_covers(series_info, chapters)


def is_mangadex_url(url: str) -> bool:
    """
    Determine if the url given is for MangaDex

    Arguments:
        url (str): the string to test

    Returns:
        (bool): true if the string is a valid MangaDex url, false otherwise
    """
    return bool(
        re.match(
            r"^(?:http(s)?:\/\/)?mangadex\.org\/?",
            url,
        )
        if mangadex_dlz.is_url(url)
        else False
    )


def get_mangadex_resource(url: str) -> Tuple[str, str]:
    """
    Gets the resource and its type from a mangadex url

    Arguments:
        url (str): the url to get the needed information from

    Returns:
        (Tuple[str, str]): a tuple containing the type of resource and the UUID of the resource
        For example:
        ("title", "a96676e5-8ae2-425e-b549-7f15dd34a6d8")
    """
    mangadex_type = ""
    resource = ""

    search = re.search(
        r"^(?:http(s)?:\/\/)?mangadex\.org\/([\w]+)\/"
        r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\/?",
        url,
    )
    try:
        mangadex_type = search.group(2)
        resource = search.group(3)

    except AttributeError as err:
        raise ValueError("Could not get resource type or resource UUID!") from err

    return (mangadex_type, resource)
