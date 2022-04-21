import unittest
import warnings
from datetime import date

import mangadex_dlz


class TestUtils(unittest.TestCase):
    def setUp(self):
        self.chapter = {
            "id": "alpha",
            "series_id": "beta",
            "chapter": 1.0,
            "volume": 2,
            "title": "charlie",
            "published_time": "2022-04-14T14:42:30+00:00",
        }
        self.series = {
            "id": "delta",
            "title": "echo",
            "description": "foxtrot",
            "year": 2000,
            "author": "golf",
        }

        self.expected_comicinfo = {
            "Title": "charlie",
            "Series": "echo",
            "Summary": "foxtrot",
            "Number": "1",
            "Year": 2022,
            "Month": 4,
            "Day": 14,
            "Writer": "golf",
            "Manga": "YesAndRightToLeft",
        }

    def test_is_url(self):
        self.assertTrue(mangadex_dlz.is_url("https://mangadex.org"))
        self.assertTrue(mangadex_dlz.is_url("https://www.google.com"))
        self.assertFalse(mangadex_dlz.is_url("./test/test.jpg"))

    def test_create_comicinfo_json(self):
        self.assertDictEqual(
            mangadex_dlz.create_comicinfo_json(self.chapter, self.series),
            self.expected_comicinfo,
        )

    def test_create_comicinfo_json_float_chapter(self):
        self.chapter["chapter"] = 1.5
        self.expected_comicinfo["Number"] = "1.5"

        self.assertDictEqual(
            mangadex_dlz.create_comicinfo_json(self.chapter, self.series),
            self.expected_comicinfo,
        )

    def test_create_comicinfo_json_no_year(self):
        self.series["year"] = None
        self.expected_comicinfo["Year"] = date.today().year

        self.assertDictEqual(
            mangadex_dlz.create_comicinfo_json(self.chapter, self.series),
            self.expected_comicinfo,
        )

    def test_downscale_if_too_small(self):
        warnings.warn("Test not implemented")

    def test_make_name_safe(self):
        self.assertEqual(
            mangadex_dlz.make_name_safe("!@#$%^&*()_+-=[]{}:;,<.>/?|\\ "),
            "____________-_________._____ ",
        )


if __name__ == "__main__":
    unittest.main()
