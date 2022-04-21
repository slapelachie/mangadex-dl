"""Typehints defined for mangadex_dl"""
from typing import TypedDict, Dict


class ChapterInfo(TypedDict):
    """Typehint for chapter info dictionary"""

    id: str
    series_id: str
    chapter: float
    volume: int
    title: str
    publish_time: str


class SeriesInfo(TypedDict):
    """
    Typehint for series info return.
    Example: {"id": "a96676e5-8ae2-425e-b549-7f15dd34a6d8",
              "title": "Komi-san wa Komyushou Desu.",
              "description": "Komi-san is a beautiful and...", # truncated for readability
              "year": 2016,
              "author": "Oda Tomohito",
              "cover_art_url": "https://uploads.mangadex.org/..."} # truncated for readability
    """

    id: str
    title: str
    description: str
    year: int
    author: str
    cover_art_url: str


class VolumeInfo(TypedDict):
    """Typehint for volume"""

    volume: str
    chapters: Dict


class ReportInfo(TypedDict):
    """typehint for mangadex reports"""

    url: str
    success: bool
    bytes: int
    cached: bool
    duration: int


class ComicInfo(TypedDict):
    """Typehint for comicinfo data structure"""

    Title: str
    Series: str
    Summary: str
    Number: float
    Year: int
    Writer: str
    Manga: str
