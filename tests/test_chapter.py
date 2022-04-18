import unittest
import warnings

import requests

import mangadex_dl


class TestChapter(unittest.TestCase):
    def test_get_chapter_info(self):
        expected_keys = ["id", "series_id", "chapter", "volume", "title"]
        chapter_info = mangadex_dl.chapter.get_chapter_info(
            "e86ec2c4-c5e4-4710-bfaa-7604f00939c7"
        )

        self.assertEqual(len(chapter_info), 5)

        self.assertTrue(all(key in chapter_info for key in expected_keys))

        self.assertIsInstance(chapter_info.get("id"), str)
        self.assertIsInstance(chapter_info.get("series_id"), str)
        self.assertIsInstance(chapter_info.get("chapter"), float)
        self.assertIsInstance(chapter_info.get("volume"), int)
        self.assertIsInstance(chapter_info.get("title"), str)

    def test_get_chapter_info_bad_id(self):
        with self.assertRaises(requests.RequestException):
            _ = mangadex_dl.chapter.get_chapter_info(
                "e86ec2c4-c5e4-4710-bfaa-7604f00939c9"
            )

    def test_get_chapter_info_bad_key(self):
        warnings.warn("Test not implemented")

    def test_get_chapter_image_urls(self):
        chapter_urls = mangadex_dl.chapter.get_chapter_image_urls(
            "e86ec2c4-c5e4-4710-bfaa-7604f00939c7"
        )

        self.assertGreater(len(chapter_urls), 0)
        for url in chapter_urls:
            self.assertIsInstance(url, str)

    def test_get_chapter_image_urls_bad_id(self):
        with self.assertRaises(requests.RequestException):
            _ = mangadex_dl.chapter.get_chapter_image_urls(
                "e86ec2c4-c5e4-4710-bfaa-7604f00939c9"
            )

    def test_get_chapter_image_urls_bad_data(self):
        warnings.warn("Test not implemented")

    def test_get_chapter_directory(self):
        self.assertEqual(
            mangadex_dl.chapter.get_chapter_directory(2.0, "bar"), "002 bar"
        )
        self.assertEqual(
            mangadex_dl.chapter.get_chapter_directory(2.5, "bar"),
            "002.5 bar",
        )

    def test_get_chapter_directory_nan(self):
        with self.assertRaises(TypeError):
            _ = mangadex_dl.chapter.get_chapter_directory("foobar", "bar")

    def test_download_chapter_image(self):
        warnings.warn("Test not implemented")

    def test_download_chapter(self):
        warnings.warn("Test not implemented")

    def test_get_chapter_cache(self):
        warnings.warn("Test not implmented")

    def test_get_ids_not_excluded_chapters(self):
        grouped_ids = [["a", "b"], ["c", "d"], ["e", "f"]]
        excluded_ids = ["c"]

        self.assertListEqual(
            mangadex_dl.chapter.get_ids_not_excluded_chapters(
                grouped_ids, excluded_ids
            ),
            ["a", "e"],
        )

    def test_get_ids_matched(self):
        grouped_ids = [["a", "b"], ["c", "d"], ["e", "f"]]
        excluded_ids = ["c", "f", "g", "k"]

        self.assertListEqual(
            mangadex_dl.chapter.get_ids_matched(grouped_ids, excluded_ids), ["c", "f"]
        )


if __name__ == "__main__":
    unittest.main()
