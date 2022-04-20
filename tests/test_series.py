import unittest
import warnings
import json
from datetime import date

import requests

import mangadex_dlz


class TestSeries(unittest.TestCase):
    def setUp(self):
        self.attributes = {
            "title": {"en": "alpha", "ja-ro": "beta", "ja": "charlie"},
            "id": "delta",
            "description": {"en": "echo", "ja": "foxtrot"},
            "year": 2000,
        }

        self.relationships = [
            {"type": "golf", "attributes": {"name": "hotel"}},
            {"type": "author", "attributes": {"name": "india"}},
            {"type": "cover_art", "attributes": {"fileName": "juliett"}},
        ]

    def test_get_series_title(self):
        title_info = self.attributes["title"]
        self.assertEqual(mangadex_dlz.series.get_series_title(title_info), "alpha")

    def test_get_series_author(self):
        self.assertEqual(
            mangadex_dlz.series.get_series_author(self.relationships), "india"
        )

    def test_get_series_author_no_relationships(self):
        self.assertEqual(mangadex_dlz.series.get_series_author([]), "No Author")

    def test_get_series_cover_art_url(self):
        self.assertEqual(
            mangadex_dlz.series.get_series_cover_art_url("delta", self.relationships),
            "https://uploads.mangadex.org/covers/delta/juliett.512.jpg",
        )

    def test_parse_series_info(self):
        expected = {
            "id": "delta",
            "title": "alpha",
            "description": "echo",
            "year": 2000,
            "author": "india",
            "cover_art_url": "https://uploads.mangadex.org/covers/delta/juliett.512.jpg",
        }

        self.assertDictEqual(
            mangadex_dlz.series.parse_series_info(
                "delta", self.attributes, self.relationships
            ),
            expected,
        )

    def test_parse_series_info_no_description(self):
        self.attributes["description"] = {"ja": "foxtrot"}
        expected = {
            "id": "delta",
            "title": "alpha",
            "description": "",
            "year": 2000,
            "author": "india",
            "cover_art_url": "https://uploads.mangadex.org/covers/delta/juliett.512.jpg",
        }

        self.assertDictEqual(
            mangadex_dlz.series.parse_series_info(
                "delta", self.attributes, self.relationships
            ),
            expected,
        )

    def test_parse_series_info_no_date(self):
        self.attributes["year"] = None
        expected = {
            "id": "delta",
            "title": "alpha",
            "description": "echo",
            "year": date.today().year,
            "author": "india",
            "cover_art_url": "https://uploads.mangadex.org/covers/delta/juliett.512.jpg",
        }

        self.assertDictEqual(
            mangadex_dlz.series.parse_series_info(
                "delta", self.attributes, self.relationships
            ),
            expected,
        )

    def test_get_seroes_info_bad_id(self):
        with self.assertRaises(requests.RequestException):
            _ = mangadex_dlz.series.get_series_info(
                "e86ec2c4-c5e4-4710-bfaa-7604f00939c9"
            )

    def test_get_grouped_chapter_ids_from_volumes(self):
        volumes = {"1": {"1": ["a", "e"], "2": ["b"]}, "2": {"3": ["c"], "4": ["d"]}}
        self.assertListEqual(
            mangadex_dlz.series.get_grouped_chapter_ids_from_volumes(volumes),
            [["a", "e"], ["b"], ["c"], ["d"]],
        )

    def test_process_mangadex_volumes(self):
        with open("tests/assets/mangadex_volume.json", "r", encoding="utf-8") as fin:
            mangadex_volumes = json.load(fin)
            self.assertDictEqual(
                mangadex_dlz.series.process_mangadex_volumes(mangadex_volumes),
                {
                    "1": {
                        "1": [
                            "1615adcb-5167-4459-8b12-ee7cfbdb10d9",
                            "3fcf382d-cf20-4e52-8ebf-cbb10272fca9",
                        ],
                        "2": ["ceab7438-866d-476c-9943-fa3fa3999f49"],
                    },
                    "2": {
                        "3": ["ddfc1bae-3729-490c-bd58-25f8441b74ec"],
                        "4": ["4c3d0be7-e85f-49c2-8037-df42850e3ff6"],
                    },
                },
            )

        _ = mangadex_dlz.series.process_mangadex_volumes(
            {
                "1": {
                    "volume": "1",
                    "count": 2,
                    "chapters": {
                        "1": {"chapter": "1", "id": "foo", "others": [], "count": 1}
                    },
                }
            }
        )

    def test_process_mangadex_volumes_empty(self):
        self.assertDictEqual(mangadex_dlz.series.process_mangadex_volumes({}), {})

    def test_process_mangadex_volumes_empty_volume(self):
        self.assertDictEqual(
            mangadex_dlz.series.process_mangadex_volumes(
                {"1": {"volume": "1", "count": 2, "chapters": {}}}
            ),
            {},
        )


if __name__ == "__main__":
    unittest.main()
