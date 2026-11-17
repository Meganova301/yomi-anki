import unittest
from unittest.mock import patch

from main import main


class TestMain(unittest.TestCase):

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
        mock_images
    ):
        mock_read_words.return_value = ["見逃す"]
        mock_anki.return_value.get_existing_words.return_value = {
            "見逃す"
        }
        mock_anki.return_value.note_exists.return_value = True

        main()

        mock_yomitan.return_value.lookup_word.assert_not_called()
        mock_generator.return_value.generate_example.assert_not_called()
        mock_images.return_value.search_image.assert_not_called()
        mock_anki.return_value.create_note.assert_not_called()


if __name__ == "__main__":
    unittest.main()
