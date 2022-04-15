import unittest
import warnings
import mangadex_dl


class TestUtils(unittest.TestCase):
    def test_is_url(self):
        self.assertTrue(mangadex_dl.is_url("https://mangadex.org"))
        self.assertTrue(mangadex_dl.is_url("https://www.google.com"))
        self.assertFalse(mangadex_dl.is_url("./test/test.jpg"))

    def test_is_mangadex_url(self):
        self.assertTrue(mangadex_dl.is_mangadex_url("https://mangadex.org"))
        self.assertFalse(mangadex_dl.is_mangadex_url("https://www.google.com"))
        self.assertFalse(mangadex_dl.is_mangadex_url("./test/test.jpg"))

    def test_get_mangadex_resource_title(self):
        mangadex_type, resource = mangadex_dl.get_mangadex_resource(
            "https://mangadex.org/title/a96676e5-8ae2-425e-b549-7f15dd34a6d8/komi-san-wa-komyushou-desu"
        )

        mangadex_type_nt, resource_nt = mangadex_dl.get_mangadex_resource(
            "https://mangadex.org/title/a96676e5-8ae2-425e-b549-7f15dd34a6d8"
        )
        self.assertEqual(mangadex_type, "title")
        self.assertEqual(mangadex_type_nt, "title")
        self.assertEqual(resource, "a96676e5-8ae2-425e-b549-7f15dd34a6d8")
        self.assertEqual(resource_nt, "a96676e5-8ae2-425e-b549-7f15dd34a6d8")

    def test_get_mangadex_resource_chapter(self):
        mangadex_type, resource = mangadex_dl.get_mangadex_resource(
            "https://mangadex.org/chapter/56eecc6f-1a4e-464c-b6a4-a1cbdfdfd726"
        )
        self.assertEqual(mangadex_type, "chapter")
        self.assertEqual(resource, "56eecc6f-1a4e-464c-b6a4-a1cbdfdfd726")

    def test_get_mangadex_resource_no_uuid(self):
        with self.assertRaises(ValueError):
            _ = (mangadex_dl.get_mangadex_resource("https://mangadex.org/chapter"),)

    def test_get_mangadex_resource_no_resource(self):
        with self.assertRaises(ValueError):
            _ = (
                mangadex_dl.get_mangadex_resource(
                    "https://mangadex.org/56eecc6f-1a4e-464c-b6a4-a1cbdfdfd726"
                ),
            )

    def test_get_mangadex_request(self):
        warnings.warn("Test not implemented")

    def test_get_mangadex_respons(self):
        warnings.warn("Test not implemented")

    def test_create_cbz(self):
        warnings.warn("Test not implemented")

    def test_create_comicinfo(self):
        warnings.warn("Test not implemented")


if __name__ == "__main__":
    unittest.main()
