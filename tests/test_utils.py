import unittest
import warnings
import mangadex_dl


class TestUtils(unittest.TestCase):
    def test_is_url(self):
        self.assertTrue(mangadex_dl.is_url("https://mangadex.org"))
        self.assertTrue(mangadex_dl.is_url("https://www.google.com"))
        self.assertFalse(mangadex_dl.is_url("./test/test.jpg"))

    def test_get_mangadex_request(self):
        warnings.warn("Test not implemented")

    def test_get_mangadex_response(self):
        warnings.warn("Test not implemented")

    def test_create_cbz(self):
        warnings.warn("Test not implemented")

    def test_create_comicinfo(self):
        warnings.warn("Test not implemented")

    def test_download_image(self):
        warnings.warn("Test not implemented")

    def test_get_image_data(self):
        warnings.warn("Test not implemented")

    def test_make_name_safe(self):
        self.assertEqual(
            mangadex_dl.make_name_safe("!@#$%^&*()_+-=[]{}:;,<.>/?|\\ "),
            "____________-_________._____ ",
        )


if __name__ == "__main__":
    unittest.main()
