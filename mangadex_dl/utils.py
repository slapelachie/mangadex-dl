"""
Random utilities for mangadex_dl
"""
import re
import shutil
import os
from time import sleep, time
from typing import Dict

import requests
from dict2xml import dict2xml


def is_url(url: str) -> bool:
    """
    Determine if a string is a URL

    Arguments:
        url (str): the string to test

    Returns:
        (bool): true if the string is a valid url, false otherwise
    """
    return bool(
        re.match(
            r"^(?:http(s)?:\/\/)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+$",
            url,
        )
    )


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
            r"^(?:http(s)?:\/\/)?mangadex\.org\/([\w\-/?#&=]+)?",
            url,
        )
        if is_url(url)
        else False
    )


def get_mangadex_resource(url: str):
    search = re.search(
        r"^((http[s]?|ftp):\/)?\/?([^:\/\s]+)((\/\w+)*\/)([\w\-\.]+[^#?\s]+)(.*)?(#[\w\-]+)?$",
        url,
    )
    mangadex_type = search.group(4).replace("/", "")

    resource = re.search(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", url
    ).group(0)

    return [mangadex_type, resource]


def get_mangadex_request(url: str):
    response = requests.get(url)

    while response.status_code == 429:
        wait_time = int(
            int(response.headers.get("x-ratelimit-retry-after", int(time() + 60)))
            - time()
        )

        print(f"Exceeded rate-limit, waiting {wait_time} seconds")
        sleep(wait_time)

        response = requests.get(url)

    if response.status_code != 200:
        raise ValueError("Response was not successfull!")

    sleep(1)
    return response


def get_mangadex_response(url: str):
    response = get_mangadex_request(url)
    return response.json()


def create_cbz(chapter_directory: str):
    shutil.make_archive(chapter_directory, "zip", chapter_directory)
    shutil.move(
        f"{chapter_directory}.zip",
        f"{chapter_directory}.cbz",
    )


def create_comicinfo(out_directory: str, chapter: Dict, series: Dict):
    data = {
        "ComicInfo": {
            "Title": chapter.get("title"),
            "Series": series.get("title"),
            "Summary": series.get("description"),
            "Number": chapter.get("chapter"),
            "Year": series.get("year"),
            "Writer": series.get("author"),
            "Manga": "YesAndRightToLeft",
        }
    }
    xml = dict2xml(data)
    with open(
        os.path.join(out_directory, "ComicInfo.xml"), "w+", encoding="utf-8"
    ) as fout:
        fout.write(xml)
