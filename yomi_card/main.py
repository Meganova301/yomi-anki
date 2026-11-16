
from config import WORDS_FILE
from src.input_manager import read_words
from src.yomitan_client import YomitanClient
from src.anki_client import AnkiClient
from src.sentence_generator import SentenceGenerator


def main():
    words = read_words(WORDS_FILE)

    yomitan = YomitanClient()
    anki = AnkiClient()
    generator = SentenceGenerator()

    for word in words:
        print(f"\nProcessing: {word}")

        raw_data = yomitan.lookup_word(word)
        word_data = yomitan.parse_entry(raw_data)

        if not word_data:
            print("No dictionary entry found.")
            continue

        audio = yomitan.get_audio(
            word_data["word"],
            word_data["reading"]
        )

        if not audio:
            print("No matching Yomitan audio found.")
            continue

        example = generator.generate_example(
            word_data["word"],
            word_data["reading"],
            word_data["definition"]
        )

        note_id = anki.create_note(
            word_data,
            audio=audio,
            example=example
        )

        print(f"Japanese: {example['japanese']}")
        print(f"English: {example['english']}")
        print(f"Created Anki note: {note_id}")


if __name__ == "__main__":
    main()
