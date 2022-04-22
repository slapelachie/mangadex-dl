import os
import re
import logging
from typing import List
from multiprocessing.dummy import Pool

import tqdm

from mangadex_dlz import download_image
from mangadex_dlz import chapter as md_chapter
from mangadex_dlz.exceptions import ExternalChapterError
from mangadex_dlz.logger_utils import TqdmLoggingHandler

THREAD_COUNT = 5

logger = logging.getLogger(__name__)
logger.addHandler(TqdmLoggingHandler())
logger.propagate = False


class ThreadedRequest:
    def __init__(self, progress_bars: bool = False, progress_desc: str = None):
        self._progress_bars = progress_bars
        self._progress_desc = progress_desc
        self._threads = THREAD_COUNT

    def _get_chapter(self, chapter_id: str):
        try:
            return md_chapter.get_chapter_info(chapter_id)
        except ExternalChapterError:
            logger.info("Chapter is from an external source, skipping...")

        return None

    def get_chapters(self, chapter_ids: List[str]):
        pool = Pool(self._threads)
        results = tqdm.tqdm(
            pool.imap(self._get_chapter, chapter_ids),
            ascii=True,
            desc="Chapter Info",
            disable=not self._progress_bars,
            position=1,
            leave=False,
            total=len(chapter_ids),
        )
        outputs = tuple(results)

        pool.close()
        pool.join()
        return [result for result in outputs if result is not None]


class ThreadedDownloader:
    def __init__(
        self,
        output_directory: str,
        enable_reporting: bool = False,
        progress_bars: bool = False,
        progress_desc: str = None,
    ):
        self._output_directory = output_directory
        self._enable_reporting = enable_reporting
        self._progress_bars = progress_bars
        self._progress_desc = progress_desc
        self._threads = THREAD_COUNT

    def _download_chapter(self, url: str):
        chapter_number = extract_page_number_from_filename(os.path.basename(url))
        file_path = os.path.join(self._output_directory, f"{chapter_number:03}.jpg")
        download_image(url, file_path, enable_reporting=self._enable_reporting)

    def download_chapter(self, urls: str):
        pool = Pool(self._threads)
        result = tqdm.tqdm(
            pool.imap(self._download_chapter, urls),
            ascii=True,
            desc=self._progress_desc,
            leave=False,
            disable=not self._progress_bars,
            position=0,
            total=len(urls),
        )
        tuple(result)

        pool.close()
        pool.join()


def extract_page_number_from_filename(filename: str):
    search = re.search(r"[a-zA-Z]?([0-9]{1,})-", filename)
    try:
        image_number = search.group(1) or "0"
    except AttributeError:
        return 0

    return int(image_number)
