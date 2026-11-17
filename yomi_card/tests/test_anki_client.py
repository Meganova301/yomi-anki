import unittest
from unittest.mock import patch

from src.anki_client import AnkiClient


class TestAnkiClient(unittest.TestCase):

    @patch.object(AnkiClient, "request")
    def test_validate_destination_checks_deck_model_and_fields(
        self,
        mock_request,
    ):
        mock_request.side_effect = [
            ["YomiCardV2"],
            ["Kaishi 1.5k"],
            [
                "Word",
                "Word Reading",
                "Word Meaning",
                "Word Furigana",
                "Word Audio",
                "Sentence",
                "Sentence Meaning",
                "Sentence Furigana",
                "Sentence Audio",
                "Notes",
                "Pitch Accent",
                "Pitch Accent Notes",
                "Frequency",
                "Picture",
            ],
        ]

        AnkiClient().validate_destination()

        self.assertEqual(mock_request.call_count, 3)
        mock_request.assert_any_call(
            "modelFieldNames",
            {"modelName": "Kaishi 1.5k"},
        )

    @patch.object(AnkiClient, "request")
    def test_validate_destination_fails_before_model_lookup_if_deck_missing(
        self,
        mock_request,
    ):
        mock_request.return_value = ["Default"]

        with self.assertRaisesRegex(RuntimeError, "YomiCardV2"):
            AnkiClient().validate_destination()

        mock_request.assert_called_once_with("deckNames")

    @patch.object(AnkiClient, "request")
    def test_create_note(self, mock_request):
        mock_request.return_value = 12345

        word_data = {
            "word": "見逃す",
            "reading": "みのがす",
            "definition": "to miss; to overlook",
            "frequency": 2458,
            "furigana": "<ruby>見逃す<rt>みのがす</rt></ruby>",
            "frequency_harmonic_rank": "2458",
        }
        example = {
            "ai_definition": "to overlook",
            "japanese": "彼は手がかりを見逃した。",
            "english": "He overlooked the clue.",
        }

        client = AnkiClient()
        note_id = client.create_note(
            word_data,
            example=example,
            sentence_furigana="<ruby>彼<rt>かれ</rt></ruby>は",
        )

        self.assertEqual(note_id, 12345)

        action, params = mock_request.call_args.args

        self.assertEqual(action, "addNote")
        self.assertEqual(
            params["note"]["modelName"],
            "Kaishi 1.5k",
        )
        self.assertEqual(
            params["note"]["fields"]["Word"],
            "見逃す"
        )
        self.assertIn(
            "<ruby>見逃す<rt>みのがす</rt></ruby>",
            params["note"]["fields"]["Word Furigana"]
        )
        self.assertEqual(
            params["note"]["fields"]["Word Meaning"],
            "to overlook",
        )
        self.assertEqual(
            params["note"]["fields"]["Sentence Meaning"],
            "He overlooked the clue.",
        )
        self.assertNotIn("audio", params["note"])

        
    @patch.object(AnkiClient, "request")
    def test_get_existing_words(self, mock_request):
        mock_request.side_effect = [
            [101, 102],
            [
                {"fields": {"Word": {"value": "見逃す"}}},
                {"fields": {"Front": {"value": "違和感"}}}
            ]
        ]

        client = AnkiClient()
        words = client.get_existing_words()

        self.assertEqual(
            words,
            {"見逃す", "違和感"}
        )

        self.assertTrue(client.note_exists("見逃す", words))
        self.assertFalse(client.note_exists("夕焼け", words))

if __name__ == "__main__":
    unittest.main()