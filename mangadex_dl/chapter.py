import re
import os
import io
import sys
from math import floor
from typing import Dict

from PIL import Image

import mangadex_dl


def get_chapter_info(chapter_id: str):
    chapter_info = {"id": chapter_id}

    response = mangadex_dl.get_mangadex_response(
        f"https://api.mangadex.org/chapter/{chapter_id}"
    )
    data = response.get("data")

    for relationship in data.get("relationships"):
        if relationship.get("type") == "manga":
            series_id = relationship.get("id", None)
            if series_id is None:
                continue

            chapter_info["series_id"] = series_id
            break
    else:
        print("Could not get series from chapter!")
        sys.exit(1)

    chapter_info["chapter"] = data.get("attributes", {}).get("chapter", 0)
    chapter_info["volume"] = data.get("attributes", {}).get("volume", 0)

    fallback_title = f"Chapter {chapter_info['chapter']}"
    chapter_title = data.get("attributes", {}).get("title", fallback_title)

    chapter_info["title"] = chapter_title or fallback_title

    print(f'Got info for "{chapter_info["chapter"]} {chapter_info["title"]}"')

    return chapter_info


def get_chapter_image_urls(chapter_id: str):
    chapter_urls = []
    response = mangadex_dl.get_mangadex_response(
        f"https://api.mangadex.org/at-home/server/{chapter_id}"
    )

    chapter_image_data = response.get("chapter", {}).get("data")
    if chapter_image_data is None:
        print("Could not find chapter URLs")
        return []

    for chapter_image in chapter_image_data:
        base_url = response.get("baseUrl")
        chapter_hash = response.get("chapter", {}).get("hash")

        if base_url is not None and chapter_hash is not None:
            chapter_urls.append(f"{base_url}/data/{chapter_hash}/{chapter_image}")

    return chapter_urls


def get_chapter_directory(series_title: str, chapter_number: float, chapter_title: str):
    if not isinstance(chapter_number, float):
        raise TypeError()

    chapter_title = re.sub(r"[^\w\-_\. ]", "_", chapter_title)
    series_title = re.sub(
        r"[^a-z0-9\-]",
        "",
        re.sub(r"\s+", "-", re.sub(" +", " ", series_title.lower())),
    )

    return (f"{series_title}/{chapter_number:05.1f}").rstrip("0").rstrip(
        "."
    ) + f" {chapter_title}"


def download_chapter_image(url: str, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    for attempt in range(5):
        if attempt > 0:
            print("Retrying...")

        response = mangadex_dl.get_mangadex_request(url)

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


def download_chapter(file_directory: str, chapter: Dict, series: Dict):
    chapter_id = chapter.get("id")
    chapter_title = chapter.get("title")
    chapter_number = float(chapter.get("chapter", 0))
    series_id = series.get("id")

    print(f'Downloading chapter "{chapter_number} {chapter_title}"')

    image_urls = get_chapter_image_urls(chapter_id)

    for i, url in enumerate(image_urls, start=1):
        print(
            f"Downloading page {i} of chapter {series_id}: {chapter_number} ({chapter_id})"
        )
        file_path = os.path.join(file_directory, f"{i:03}.jpg")

        download_chapter_image(url, file_path)
