import unittest
from unittest.mock import patch

from src.anki_client import AnkiClient


class TestAnkiClient(unittest.TestCase):

    @patch.object(AnkiClient, "request")
    def test_create_note(self, mock_request):
        mock_request.return_value = 12345

        word_data = {
            "word": "見逃す",
            "reading": "みのがす",
            "definition": "to miss; to overlook",
            "frequency": 2458
        }

        client = AnkiClient()
        note_id = client.create_note(word_data)

        self.assertEqual(note_id, 12345)

        action, params = mock_request.call_args.args

        self.assertEqual(action, "addNote")
        self.assertEqual(
            params["note"]["fields"]["Front"],
            "見逃す"
        )
        self.assertIn(
            "みのがす",
            params["note"]["fields"]["Back"]
        )


if __name__ == "__main__":
    unittest.main()