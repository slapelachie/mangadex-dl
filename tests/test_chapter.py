import unittest

import mangadex_dlz


class TestChapter(unittest.TestCase):
    def test_get_series_id_from_series_relationships(self):
        relationships = [
            {"id": "alpha", "type": "beta"},
            {"id": "charlie", "type": "manga"},
        ]

        self.assertEqual(
            mangadex_dlz.chapter.get_series_id_from_series_relationships(relationships),
            "charlie",
        )

    def test_get_series_id_from_series_relationships_no_manga(self):
        relationships = [
            {"id": "alpha", "type": "beta"},
            {"id": "charlie", "type": "delta"},
        ]

        self.assertIsNone(
            mangadex_dlz.chapter.get_series_id_from_series_relationships(relationships)
        )

    def test_parse_chapter_info(self):
        attributes = {"volume": "1", "chapter": "1.5", "title": "alpha"}
        expected_info = {
            "id": "beta",
            "series_id": "charlie",
            "chapter": 1.5,
            "volume": 1,
            "title": "alpha",
        }

        self.assertDictEqual(
            mangadex_dlz.chapter.parse_chapter_info("beta", "charlie", attributes),
            expected_info,
        )

    def test_parse_chapter_info_bad_chapter(self):
        attributes = {"volume": "1", "chapter": "delta", "title": "alpha"}

        with self.assertRaises(ValueError):
            mangadex_dlz.chapter.parse_chapter_info("beta", "charlie", attributes)

    def test_parse_chapter_info_bad_volume(self):
        attributes = {"volume": "delta", "chapter": "1.5", "title": "alpha"}

        with self.assertRaises(ValueError):
            mangadex_dlz.chapter.parse_chapter_info("beta", "charlie", attributes)

    def test_parse_chapter_image_urls(self):
        base_url = "alpha"
        chapter_hash = "beta"
        chapter_images = ["charlie", "delta"]

        expected_urls = ["alpha/data/beta/charlie", "alpha/data/beta/delta"]

        self.assertListEqual(
            mangadex_dlz.chapter.parse_chapter_image_urls(
                base_url, chapter_hash, chapter_images
            ),
            expected_urls,
        )

    def test_get_chapter_directory(self):
        self.assertEqual(
            mangadex_dlz.chapter.get_chapter_directory(2.0, "bar"), "002 bar"
        )
        self.assertEqual(
            mangadex_dlz.chapter.get_chapter_directory(2.5, "bar"),
            "002.5 bar",
        )

    def test_get_chapter_directory_nan(self):
        with self.assertRaises(TypeError):
            _ = mangadex_dlz.chapter.get_chapter_directory("foobar", "bar")

    def test_get_ids_not_excluded_chapters(self):
        grouped_ids = [["a", "b"], ["c", "d"], ["e", "f"]]
        excluded_ids = ["c"]

        self.assertListEqual(
            mangadex_dlz.chapter.get_ids_not_excluded_chapters(
                grouped_ids, excluded_ids
            ),
            ["a", "e"],
        )

    def test_get_ids_matched(self):
        grouped_ids = [["a", "b"], ["c", "d"], ["e", "f"]]
        excluded_ids = ["c", "f", "g", "k"]

        self.assertListEqual(
            mangadex_dlz.chapter.get_ids_matched(grouped_ids, excluded_ids), ["c", "f"]
        )


if __name__ == "__main__":
    unittest.main()
