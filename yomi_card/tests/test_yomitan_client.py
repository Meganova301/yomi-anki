import unittest
from unittest.mock import patch, Mock
from src.yomitan_client import YomitanClient


class TestYomitanClient(unittest.TestCase):

    def setUp(self):
        self.client = YomitanClient()

    def test_empty_entries(self):
        result = self.client.parse_entry({"dictionaryEntries": []})
        self.assertIsNone(result)

    def test_missing_headwords(self):
        data = {
            "dictionaryEntries": [
                {"headwords": [], "definitions": []}
            ]
        }

        result = self.client.parse_entry(data)
        self.assertEqual(result["word"], "")
        self.assertEqual(result["reading"], "")
        self.assertEqual(result["definition"], "")
        self.assertIsNone(result["frequency"])
    @patch("src.yomitan_client.requests.post")
    def test_get_audio(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            "fields": [
                {
                    "expression": "見逃す",
                    "reading": "みのがす",
                    "audio": "[sound:test.mp3]"
                }
            ],
            "audioMedia": [
                {
                    "ankiFilename": "test.mp3",
                    "content": "base64_audio_data"
                }
            ]
        }

        mock_post.return_value = mock_response

        audio = self.client.get_audio("見逃す", "みのがす")

        self.assertEqual(audio["filename"], "test.mp3")
        self.assertEqual(audio["data"], "base64_audio_data")
        self.assertEqual(audio["fields"], ["Back"])

    @patch("src.yomitan_client.requests.post")
    def test_audio_not_found(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            "fields": [],
            "audioMedia": []
        }

        mock_post.return_value = mock_response

        audio = self.client.get_audio("見逃す", "みのがす")

        self.assertIsNone(audio)

if __name__ == "__main__":
    unittest.main()