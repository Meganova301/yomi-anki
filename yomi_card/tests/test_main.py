import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from main import main


class TestMain(unittest.TestCase):

    def configure_successful_word(
        self,
        mock_yomitan,
        mock_anki,
        mock_generator,
        mock_images,
    ):
        mock_yomitan.return_value.parse_entry.return_value = {
            "word": "見逃す",
            "reading": "みのがす",
            "definition": "to overlook",
            "frequency": 100,
        }
        mock_yomitan.return_value.get_term_card_data.return_value = {
            "audio": {
                "filename": "audio.mp3",
                "data": "audio-data",
                "fields": ["Word Audio"],
            },
            "furigana": "<ruby>見逃す<rt>みのがす</rt></ruby>",
            "frequency_harmonic_rank": "2458",
        }
        mock_yomitan.return_value.get_sentence_furigana.return_value = (
            "<ruby>彼<rt>かれ</rt></ruby>は"
        )
        mock_generator.return_value.generate_example.return_value = {
            "ai_definition": "to overlook",
            "japanese": "彼は手がかりを見逃した。",
            "english": "He overlooked the clue.",
            "image_query": "detective examining clues",
        }
        mock_images.return_value.search_image.return_value = None
        mock_anki.return_value.create_note.return_value = 123

    def configure_duplicate_check(self, mock_anki):
        mock_anki.return_value.note_exists.side_effect = (
            lambda word, existing_words: word in existing_words
        )

    @patch("main.ImageProvider")
    @patch("main.SentenceGenerator")
    @patch("main.AnkiClient")
    @patch("main.YomitanClient")
    @patch("main.read_words")
    def test_missing_anki_destination_stops_before_external_processing(
        self,
        mock_read_words,
        mock_yomitan,
        mock_anki,
        mock_generator,
        mock_images,
    ):
        mock_read_words.return_value = ["見逃す"]
        mock_anki.return_value.validate_destination.side_effect = RuntimeError(
            "Anki deck 'YomiCardV2' was not found."
        )

        with self.assertRaisesRegex(RuntimeError, "YomiCardV2"):
            main()

        mock_anki.return_value.get_existing_words.assert_not_called()
        mock_yomitan.assert_not_called()
        mock_generator.assert_not_called()
        mock_images.assert_not_called()

    @patch("main.ImageProvider")
    @patch("main.SentenceGenerator")
    @patch("main.AnkiClient")
    @patch("main.YomitanClient")
    @patch("main.read_words")
    def test_existing_word_is_skipped(
        self,
        mock_read_words,
        mock_yomitan,
        mock_anki,
        mock_generator,
        mock_images,
    ):
        mock_read_words.return_value = ["見逃す"]
        mock_anki.return_value.get_existing_words.return_value = {"見逃す"}
        self.configure_duplicate_check(mock_anki)

        with redirect_stdout(StringIO()):
            main()

        mock_anki.return_value.get_existing_words.assert_called_once()
        mock_yomitan.return_value.lookup_word.assert_not_called()
        mock_generator.return_value.generate_example.assert_not_called()
        mock_images.return_value.search_image.assert_not_called()
        mock_anki.return_value.create_note.assert_not_called()

    @patch("main.ImageProvider")
    @patch("main.SentenceGenerator")
    @patch("main.AnkiClient")
    @patch("main.YomitanClient")
    @patch("main.read_words")
    def test_created_word_is_skipped_if_repeated_in_input(
        self,
        mock_read_words,
        mock_yomitan,
        mock_anki,
        mock_generator,
        mock_images,
    ):
        mock_read_words.return_value = ["見逃す", "見逃す"]
        mock_anki.return_value.get_existing_words.return_value = set()
        self.configure_duplicate_check(mock_anki)
        self.configure_successful_word(
            mock_yomitan, mock_anki, mock_generator, mock_images
        )

        output = StringIO()
        with redirect_stdout(output):
            main()

        mock_yomitan.return_value.lookup_word.assert_called_once_with("見逃す")
        mock_generator.return_value.generate_example.assert_called_once()
        mock_anki.return_value.create_note.assert_called_once()
        self.assertIn("Created: 1", output.getvalue())
        self.assertIn("Skipped: 1", output.getvalue())
        self.assertIn("Failed:  0", output.getvalue())

    @patch("main.ImageProvider")
    @patch("main.SentenceGenerator")
    @patch("main.AnkiClient")
    @patch("main.YomitanClient")
    @patch("main.read_words")
    def test_failure_does_not_stop_later_words(
        self,
        mock_read_words,
        mock_yomitan,
        mock_anki,
        mock_generator,
        mock_images,
    ):
        mock_read_words.return_value = ["失敗語", "見逃す"]
        mock_anki.return_value.get_existing_words.return_value = set()
        self.configure_duplicate_check(mock_anki)
        self.configure_successful_word(
            mock_yomitan, mock_anki, mock_generator, mock_images
        )
        mock_yomitan.return_value.lookup_word.side_effect = [
            RuntimeError("temporary failure"),
            {"dictionaryEntries": []},
        ]

        # The second word gets a dictionary entry and can complete normally.
        mock_yomitan.return_value.parse_entry.return_value = {
            "word": "見逃す",
            "reading": "みのがす",
            "definition": "to overlook",
            "frequency": 100,
        }

        output = StringIO()
        with redirect_stdout(output):
            main()

        self.assertEqual(
            mock_yomitan.return_value.lookup_word.call_count,
            2,
        )
        mock_anki.return_value.create_note.assert_called_once()
        self.assertIn("Created: 1", output.getvalue())
        self.assertIn("Failed:  1", output.getvalue())


if __name__ == "__main__":
    unittest.main()
