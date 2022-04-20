"""Module containing the custom exceptions used by mangadex_dl"""


class BadChapterData(Exception):
    """Raised when data retreieved for data is bad"""


class FailedImageError(Exception):
    """Raised when image fails to download or be processed"""


class ComicInfoError(Exception):
    """Raised when ComicInfo.xml fails to be created"""


class ExternalChapterError(Exception):
    """Raised when the chapter is externally sourced so it couldn't be downloaded"""
