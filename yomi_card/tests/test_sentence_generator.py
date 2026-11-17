
import json
import unittest
from unittest.mock import Mock

from src.sentence_generator import SentenceGenerator
from google.genai.errors import APIError

class TestSentenceGenerator(unittest.TestCase):

    def setUp(self):
        self.generator = SentenceGenerator.__new__(
            SentenceGenerator
        )
        self.generator.client = Mock()

    def test_generate_example(self):
        expected = {
            "ai_definition": "to overlook",
            "japanese": "彼は手がかりを見逃した。",
            "english": "He overlooked the clue.",
            "image_query": "detective examining clues"
        }

        response = Mock()
        response.text = json.dumps(expected)

        self.generator.client.models.generate_content.return_value = response

        result = self.generator.generate_example(
            "見逃す",
            "みのがす",
            "to overlook"
        )

        self.assertEqual(result, expected)

    def test_empty_response(self):
        response = Mock()
        response.text = ""

        self.generator.client.models.generate_content.return_value = response

        with self.assertRaises(ValueError):
            self.generator.generate_example(
                "見逃す",
                "みのがす",
                "to overlook"
            )
    def test_api_error_is_converted_to_runtime_error(self):
        self.generator.client.models.generate_content.side_effect = APIError(
            503,
            {"message": "Service unavailable"},
        )

        with self.assertRaisesRegex(RuntimeError, "Gemini request failed"):
            self.generator.generate_example(
                "見逃す",
                "みのがす",
                "to overlook",
            )

if __name__ == "__main__":
    unittest.main()
