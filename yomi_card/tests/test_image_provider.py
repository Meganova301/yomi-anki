
import unittest
from unittest.mock import patch, Mock

from src.image_provider import ImageProvider


class TestImageProvider(unittest.TestCase):

    @patch("src.image_provider.PIXABAY_API_KEY", "test-key")
    @patch("src.image_provider.requests.get")
    def test_search_image(self, mock_get):
        response = Mock()

        response.json.return_value = {
            "hits": [
                {
                    "id": 123,
                    "webformatURL": "https://example.com/photo.jpg",
                    "user": "Photographer",
                    "pageURL": "https://pixabay.com/photos/123"
                }
            ]
        }

        mock_get.return_value = response

        provider = ImageProvider()
        result = provider.search_image("flower")

        self.assertEqual(
            result["filename"],
            "pixabay_123.jpg"
        )
        self.assertEqual(
            result["url"],
            "https://example.com/photo.jpg"
        )

    @patch("src.image_provider.requests.get")
    def test_download_image(self, mock_get):
        response = Mock()
        response.content = b"fake-image-data"
        response.headers = {"Content-Type": "image/jpeg"}

        mock_get.return_value = response

        provider = ImageProvider()

        result = provider.download_image({
            "url": "https://example.com/photo.jpg",
            "filename": "test.jpg"
        })

        self.assertEqual(result["filename"], "test.jpg")
        self.assertEqual(result["fields"], ["Picture"])
        self.assertTrue(result["data"])


if __name__ == "__main__":
    unittest.main()
