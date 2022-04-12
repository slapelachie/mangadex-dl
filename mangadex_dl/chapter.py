import re
import os
import json
import io
import shutil
from math import floor
from PIL import Image
from dict2xml import dict2xml

from mangadex_dl import utils
from mangadex_dl.series import Series

DATA_PATH = os.path.expandvars("$HOME/.cache/mangadex-dl/")
DOWNLOADED_CACHE_FILE = os.path.join(DATA_PATH, "downloaded.json")


class Chapter:
    def __init__(
        self,
        id: str,
        series: Series = None,
    ):
        self._id = id
        self._series_id = None
        self._chapter_no = None
        self._volume_no = None
        self._chapter_title = None

        self._series = series

        if self._series:
            self._series_id = self._series.get_id()

        self._get_info()

        print(f"Created new chapter {self._series_id}: {self._chapter_no} ({self._id})")

    def _get_info(self):
        print(
            f"Getting info for chapter {self._series_id}: {self._chapter_no} ({self._id})"
        )
        response = utils.get_mangadex_response(
            f"https://api.mangadex.org/chapter/{self._id}"
        )
        data = response.get("data")

        for relationship in data.get("relationships"):
            if relationship.get("type") == "manga":
                self._series_id = relationship.get("id")

        self._chapter_no = data.get("attributes").get("chapter")
        self._volume_no = data.get("attributes").get("volume")

        new_chapter_title = data.get("attributes").get("title")
        if new_chapter_title:
            re.sub(r"[^\w\-_\. ]", "_", new_chapter_title)

        self._chapter_title = new_chapter_title or f"Chapter {self._chapter_no}"

    def _get_chapter_image_urls(self):
        print(
            f"Getting image urls for chapter {self._series_id}: {self._chapter_no} ({self._id})"
        )
        chapter_urls = []
        response = utils.get_mangadex_response(
            f"https://api.mangadex.org/at-home/server/{self._id}"
        )

        for chapter_image in response.get("chapter").get("data"):
            chapter_urls.append(
                f"{response.get('baseUrl')}/data/{response.get('chapter').get('hash')}/{chapter_image}"
            )

        return chapter_urls

    def _add_chapter_to_downloaded(self):
        ensure_cache_file_exists()
        with open(DOWNLOADED_CACHE_FILE, "r+") as f:
            file_data = json.load(f)
            file_data.append(self._id)
            f.seek(0)
            json.dump(file_data, f, indent=4)

    def _create_comicinfo(self, out_directory: str):
        data = {
            "ComicInfo": {
                "Title": self._chapter_title,
                "Series": self._series.get_title(),
                "Summary": self._series.get_description(),
                "Number": self._chapter_no,
                "Year": self._series.get_year(),
                "Writer": self._series.get_author(),
                "Manga": "YesAndRightToLeft",
            }
        }
        xml = dict2xml(data)
        with open(os.path.join(out_directory, "ComicInfo.xml"), "w+") as fout:
            fout.write(xml)

    def _get_chapter_directory(self):
        series_title = re.sub(
            r"[^a-z0-9\-]",
            "",
            re.sub(r"\s+", "-", re.sub(" +", " ", self._series.get_title().lower())),
        )

        return (
            f"{series_title}/{float(self._chapter_no):05.1f}".rstrip("0").rstrip(".")
            + f" {self._chapter_title}"
        )

    def get_id(self):
        return self._id

    def download(self, directory: str):
        print(f"Downloading chapter {self._series_id}: {self._chapter_no} ({self._id})")

        image_urls = self._get_chapter_image_urls()

        if not self._series:
            self._series = Series(self._series_id)

        file_directory = os.path.join(directory, self._get_chapter_directory())
        for i, url in enumerate(image_urls, start=1):
            print(
                f"Downloading page {i} of chapter {self._series_id}: {self._chapter_no} ({self._id})"
            )
            file_path = os.path.join(file_directory, f"{i:03}.jpg")

            download_chapter_image(url, file_path)

        self._add_chapter_to_downloaded()
        self._create_comicinfo(file_directory)
        create_cbz(file_directory)
        shutil.rmtree(file_directory)


def download_chapter_image(url: str, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    for attempt in range(5):
        if attempt > 0:
            print("Retrying...")

        response = utils.get_mangadex_request(url)

        try:
            image = Image.open(io.BytesIO(response.content))
            image = image.convert("RGB")

            width, height = image.size
            new_height = 2400
            if height > new_height:
                ratio = width / height
                new_width = floor(ratio * new_height)
                image = image.resize((new_width, new_height), Image.BICUBIC)

            image.save(path, quality=90)
            break
        except OSError:
            continue
    else:
        print("Failed to download image!")


def ensure_cache_file_exists():
    if not os.path.exists(DOWNLOADED_CACHE_FILE):
        os.makedirs(os.path.dirname(DOWNLOADED_CACHE_FILE), exist_ok=True)
        with open(DOWNLOADED_CACHE_FILE, "w+") as fout:
            json.dump([], fout, indent=4)


def create_cbz(chapter_directory: str):
    shutil.make_archive(chapter_directory, "zip", chapter_directory)
    shutil.move(
        f"{chapter_directory}.zip",
        f"{chapter_directory}.cbz",
    )


def get_chapter_cache():
    try:
        with open(DOWNLOADED_CACHE_FILE, "r") as fin:
            return json.load(fin)
    except FileNotFoundError:
        return []
