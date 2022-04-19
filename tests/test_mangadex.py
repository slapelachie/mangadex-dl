import unittest
import warnings
from mangadex_dlz import mangadex


class TestMangadexFunctions(unittest.TestCase):
    def test_is_mangadex_url(self):
        self.assertTrue(mangadex.is_mangadex_url("https://mangadex.org"))
        self.assertFalse(mangadex.is_mangadex_url("https://www.google.com"))
        self.assertFalse(mangadex.is_mangadex_url("./test/test.jpg"))

    def test_get_mangadex_resource_title(self):
        mangadex_type, resource = mangadex.get_mangadex_resource(
            "https://mangadex.org/title/a96676e5-8ae2-425e-b549-7f15dd34a6d8/komi-san-wa-komyushou-desu"
        )

        mangadex_type_nt, resource_nt = mangadex.get_mangadex_resource(
            "https://mangadex.org/title/a96676e5-8ae2-425e-b549-7f15dd34a6d8"
        )
        self.assertEqual(mangadex_type, "title")
        self.assertEqual(mangadex_type_nt, "title")
        self.assertEqual(resource, "a96676e5-8ae2-425e-b549-7f15dd34a6d8")
        self.assertEqual(resource_nt, "a96676e5-8ae2-425e-b549-7f15dd34a6d8")

    def test_get_mangadex_resource_chapter(self):
        mangadex_type, resource = mangadex.get_mangadex_resource(
            "https://mangadex.org/chapter/56eecc6f-1a4e-464c-b6a4-a1cbdfdfd726"
        )
        self.assertEqual(mangadex_type, "chapter")
        self.assertEqual(resource, "56eecc6f-1a4e-464c-b6a4-a1cbdfdfd726")

    def test_get_mangadex_resource_no_uuid(self):
        with self.assertRaises(ValueError):
            _ = (mangadex.get_mangadex_resource("https://mangadex.org/chapter"),)

    def test_get_mangadex_resource_no_resource(self):
        with self.assertRaises(ValueError):
            _ = (
                mangadex.get_mangadex_resource(
                    "https://mangadex.org/56eecc6f-1a4e-464c-b6a4-a1cbdfdfd726"
                ),
            )


class TestMangadexClass(unittest.TestCase):
    def test_download_from_mangadex_url(self):
        warnings.warn("Test not implemented")

    def test_ensure_cache_file_exists(self):
        warnings.warn("Test not implemented")

    def test_add_chapter_to_downloaded(self):
        warnings.warn("Test not implemented")

    def test_process_chapter(self):
        warnings.warn("Test not implemented")

    def test_get_excluded_chapters_from_cache(self):
        warnings.warn("Test not implemented")

    def test_download_chapter_covers(self):
        warnings.warn("Test not implemented")

    def test_get_chapters_from_volumes(self):
        warnings.warn("Test not implemented")

    def test_download_series_cover(self):
        warnings.warn("Test not implemented")

    def test_download(self):
        warnings.warn("Test not implemented")

    def test_download_series_from_id(self):
        warnings.warn("Test not implemented")

    def test_download_chapter_from_id(self):
        warnings.warn("Test not implemented")

    def test_download_covers(self):
        warnings.warn("Test not implemented")
