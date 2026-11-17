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
    def test_get_term_card_data(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            "fields": [
                {
                    "expression": "見逃す",
                    "reading": "みのがす",
                    "audio": "[sound:test.mp3]",
                    "furigana": "<ruby>見逃す<rt>みのがす</rt></ruby>",
                    "frequency-harmonic-rank": 2458,
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

        term_data = self.client.get_term_card_data("見逃す", "みのがす")

        self.assertEqual(
            term_data,
            {
                "audio": {
                    "filename": "test.mp3",
                    "data": "base64_audio_data",
                    "fields": ["Word Audio"],
                },
                "furigana": "<ruby>見逃す<rt>みのがす</rt></ruby>",
                "frequency_harmonic_rank": "2458",
            },
        )

    @patch("src.yomitan_client.requests.post")
    def test_term_card_data_not_found(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            "fields": [],
            "audioMedia": []
        }

        mock_post.return_value = mock_response

        term_data = self.client.get_term_card_data("見逃す", "みのがす")

        self.assertIsNone(term_data)

    @patch("src.yomitan_client.requests.post")
    def test_get_sentence_furigana(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "content": [
                    [{"text": "子供", "reading": "こども"}],
                    [{"text": "から", "reading": ""}],
                    [{"text": "パイロット", "reading": ""}],
                    [{"text": "に", "reading": ""}],
                    [{"text": "憧", "reading": "あこが"}],
                    [{"text": "。", "reading": ""}],
                ]
            }
        ]
        mock_post.return_value = mock_response

        result = self.client.get_sentence_furigana(
            "子供の頃からパイロットに憧れている。"
        )

        self.assertEqual(
            result,
            "<ruby>子供<rt>こども</rt></ruby>"
            "の頃からパイロットに"
            "<ruby>憧<rt>あこが</rt></ruby>"
            "れている。",
        )

if __name__ == "__main__":
    unittest.main()