import unittest
import warnings

import requests

import mangadex_dl


class TestSeries(unittest.TestCase):
    def test_get_series_info(self):
        expected_keys = ["id", "title", "description", "year", "author"]
        series_info = mangadex_dl.series.get_series_info(
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
            _ = mangadex_dl.series.get_series_info(
                "e86ec2c4-c5e4-4710-bfaa-7604f00939c9"
            )

    def test_get_series_info_bad_data(self):
        warnings.warn("Test not implemented")

    def test_get_series_chapters(self):
        warnings.warn("Test not implemented")


if __name__ == "__main__":
    unittest.main()
