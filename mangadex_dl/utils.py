"""
Random utilities for mangadex_dl
"""
import re
import shutil
import os
import logging
from time import sleep, time
from typing import Dict, Tuple

import requests
from dict2xml import dict2xml

logger = logging.getLogger(__name__)


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


def get_mangadex_resource(url: str) -> Tuple[str, str]:
    """
    Gets the resource and its type from a mangadex url

    Arguments:
        url (str): the url to get the needed information from

    Returns:
        (Tuple[str, str]): a tuple containing the type of resource and the UUID of the resource
    """
    mangadex_type = ""
    resource = ""

    try:
        # Get the type from the url
        search = re.search(
            r"^((http[s]?|ftp):\/)?\/?([^:\/\s]+)((\/\w+)*\/)([\w\-\.]+[^#?\s]+)(.*)?(#[\w\-]+)?$",
            url,
        )
        mangadex_type = search.group(4).replace("/", "")

        # Get the UUID from the url
        resource = re.search(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", url
        ).group(0)
    except AttributeError as err:
        raise ValueError("Could not get resource type or resource UUID!") from err

    return (mangadex_type, resource)


def get_mangadex_request(url: str) -> requests.Response:
    """
    Perform a request to the mangadex server with the appropiate rules in place (rate limiting etc)

    Arguments:
        url (str): the url to perform the request on

    Returns:
        (requests.Response): the response from the server

    Raises:
        (requests.HTTPError): if the url does not return a valid response
    """
    response = requests.get(url)

    while response.status_code == 429:
        wait_time = int(
            int(response.headers.get("x-ratelimit-retry-after", int(time() + 60)))
            - time()
        )

        logger.warning("Exceeded rate-limit, waiting %i seconds", wait_time)
        sleep(wait_time)

        response = requests.get(url)

    if response.status_code != 200:
        response.raise_for_status()

    sleep(0.5)
    return response


def get_mangadex_response(url: str) -> Dict:
    """
    Gets the response from get_mangadex_request but in the json format
    I wrote a lot of code relying on this before I moved it to the afformentioned function, and
    didn't want to update all the references

    Arguments:
        url (str): the url to perform the request to

    Returns:
        (Dict?): the response in json format
    """
    response = get_mangadex_request(url)
    return response.json()


def create_cbz(chapter_directory: str):
    """
    Creates a CBZ archive (just a zip archive) for the given folder

    Arguments:
        chapter_directory (str): the directory to turn into a CBZ
    """
    if not os.path.isdir(chapter_directory):
        raise NotADirectoryError("The supplied path is not a directory!")

    try:
        shutil.make_archive(chapter_directory, "zip", chapter_directory)
    except shutil.Error as err:
        raise OSError(f"Failed to make archive for {chapter_directory}.zip") from err

    try:
        shutil.move(
            f"{chapter_directory}.zip",
            f"{chapter_directory}.cbz",
        )
    except shutil.Error as err:
        raise OSError(
            f"Failed to rename archive from {chapter_directory}.zip to {chapter_directory}.cbz"
        ) from err


def create_comicinfo(output_directory: str, chapter: Dict, series: Dict):
    """
    Creates a ComicInfo file for the chapter, only tested with Komago, so I have no idea if this
    works elsewhere

    Arguments:
        output_directory (str): the directory to save the file
        chapter (Dict): the chapter information (see mangadex_dl.chapter.get_chapter_info)
        series (Dict): the series information (see mangadex_dl.series.get_series_info)
    """
    if not all(key in chapter for key in ["title", "chapter"]) or not all(
        key in series for key in ["title", "description", "year", "author"]
    ):
        raise KeyError(
            "One of the needed fields in the parsed dictionaries is not valid!"
        )

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

    try:
        with open(
            os.path.join(output_directory, "ComicInfo.xml"), "w+", encoding="utf-8"
        ) as fout:
            fout.write(xml)
    except OSError as err:
        raise OSError(
            f'Could not open "{os.path.join(output_directory, "ComicInfo")}" for writing'
        ) from err
