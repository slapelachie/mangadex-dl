"""Typehints defined for mangadex_dl"""
from typing import TypedDict, Dict


class ChapterInfo(TypedDict):
    """Typehint for chapter info dictionary"""

    id: str
    series_id: str
    chapter: float
    volume: int
    title: str


class SeriesInfo(TypedDict):
    """Typehint for series info return"""

    id: str
    title: str
    description: str
    year: int
    author: str


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
