import unittest
import warnings
import json

import requests

import mangadex_dlz


class TestSeries(unittest.TestCase):
    def test_get_series_info(self):
        expected_keys = ["id", "title", "description", "year", "author"]
        series_info = mangadex_dlz.series.get_series_info(
            "a96676e5-8ae2-425e-b549-7f15dd34a6d8"
        )

        self.assertEqual(len(series_info), 6)

        self.assertTrue(all(key in series_info for key in expected_keys))

        self.assertIsInstance(series_info.get("id"), str)
        self.assertIsInstance(series_info.get("title"), str)
        self.assertIsInstance(series_info.get("description"), str)
        self.assertIsInstance(series_info.get("year"), int)
        self.assertIsInstance(series_info.get("author"), str)

    def test_get_seroes_info_bad_id(self):
        with self.assertRaises(requests.RequestException):
            _ = mangadex_dlz.series.get_series_info(
                "e86ec2c4-c5e4-4710-bfaa-7604f00939c9"
            )

    def test_get_series_info_bad_data(self):
        warnings.warn("Test not implemented")

    def test_get_series_chapters(self):
        warnings.warn("Test not implemented")

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

    def test_process_mangadex_volumes_no_volume(self):
        with self.assertRaises(KeyError):
            _ = mangadex_dlz.series.process_mangadex_volumes(
                {"1": {"count": 2, "chapters": {}}}
            )

    def test_process_mangadex_volumes_no_chapters(self):
        with self.assertRaises(KeyError):
            _ = mangadex_dlz.series.process_mangadex_volumes(
                {
                    "1": {
                        "volume": "1",
                        "count": 2,
                    }
                }
            )

    def test_process_mangadex_volumes_no_chapter(self):
        with self.assertRaises(KeyError):
            _ = mangadex_dlz.series.process_mangadex_volumes(
                {
                    "1": {
                        "volume": "1",
                        "count": 2,
                        "chapters": {"id": "foo", "others": [], "count": 1},
                    }
                }
            )

    def test_process_mangadex_volumes_no_id(self):
        with self.assertRaises(KeyError):
            _ = mangadex_dlz.series.process_mangadex_volumes(
                {
                    "1": {
                        "volume": "1",
                        "count": 2,
                        "chapters": {"chapter": "1", "others": [], "count": 1},
                    }
                }
            )

    def test_process_mangadex_volumes_no_others(self):
        with self.assertRaises(KeyError):
            _ = mangadex_dlz.series.process_mangadex_volumes(
                {
                    "1": {
                        "volume": "1",
                        "count": 2,
                        "chapters": {"chapter": "1", "id": "foo", "count": 1},
                    }
                }
            )


if __name__ == "__main__":
    unittest.main()
