"""Stop the warning"""
from mangadex_dl.utils import (
    is_url,
    get_mangadex_request,
    get_mangadex_response,
    create_cbz,
    create_comicinfo,
    download_image,
    get_image_data,
    make_name_safe,
)

from mangadex_dl.exceptions import BadChapterData, ComicInfoError, FailedImageError
from mangadex_dl.typehints import ChapterInfo, SeriesInfo, VolumeInfo
from mangadex_dl.logger_utils import TqdmLoggingHandler
from mangadex_dl.mangadex import MangaDexDL

__version__ = "1.0.0a0"
__author__ = "slapelachie"
__license__ = "GPLv2"
__email__ = "lslape@slapelachie.xyz"
__copyright__ = """Copyright (C) 2022 slapelachie
This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details."""
