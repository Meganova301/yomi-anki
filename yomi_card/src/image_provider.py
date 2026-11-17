
import base64
import requests
from src.http_utils import request_with_retries
from config import PIXABAY_API_KEY, IMAGE_TIMEOUT


class ImageProvider:

    def search_image(self, query):
        if not PIXABAY_API_KEY:
            raise ValueError("PIXABAY_API_KEY is not configured.")

        response = request_with_retries(
            requests.get,
            "https://pixabay.com/api/",
            params={
                "key": PIXABAY_API_KEY,
                "q": query[:100],
                "image_type": "all",
                "safesearch": "true",
                "per_page": 3,
            },
            timeout=IMAGE_TIMEOUT,
            retry_safe=True,
        )

        images = response.json().get("hits", [])

        if not images:
            return None

        image = images[0]

        return {
            "url": image["webformatURL"],
            "filename": f"pixabay_{image['id']}.jpg",
            "credit": f"Image by {image['user']} on Pixabay",
            "source": image["pageURL"]
        }

    def download_image(self, image):
        response = request_with_retries(
            requests.get,
            image["url"],
            timeout=IMAGE_TIMEOUT,
            retry_safe=True,
        )

        response.raise_for_status()

        content_type = response.headers.get(
            "Content-Type", ""
        )

        if not content_type.startswith("image/jpeg"):
            raise ValueError("Expected a JPEG image.")

        encoded_image = base64.b64encode(
            response.content
        ).decode("ascii")

        return {
            "filename": image["filename"],
            "data": encoded_image,
            "fields": ["Picture"]
        }
