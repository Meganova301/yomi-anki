
import requests

from config import WORDS_FILE
from src.input_manager import read_words
from src.yomitan_client import YomitanClient
from src.anki_client import AnkiClient
from src.sentence_generator import SentenceGenerator
from src.image_provider import ImageProvider


def main():
    words = read_words(WORDS_FILE)

    yomitan = YomitanClient()
    anki = AnkiClient()
    generator = SentenceGenerator()
    images = ImageProvider()

    existing_words = anki.get_existing_words()

    created = 0
    skipped = 0
    failed = 0

    total = len(words)

    for index, word in enumerate(words, start=1):
        print(f"\n[{index}/{total}] Processing: {word}")

        if anki.note_exists(word, existing_words):
            print("Skipped: Already exists in Anki.")
            skipped += 1
            continue

        try:
            raw_data = yomitan.lookup_word(word)
            word_data = yomitan.parse_entry(raw_data)

            if not word_data:
                print("Skipped: No dictionary entry.")
                skipped += 1
                continue

            if anki.note_exists(word_data["word"], existing_words):
                print("Skipped: Dictionary form already exists.")
                skipped += 1
                continue

            audio = yomitan.get_audio(
                word_data["word"],
                word_data["reading"]
            )

            if not audio:
                print("Skipped: No Yomitan audio.")
                skipped += 1
                continue

            example = generator.generate_example(
                word_data["word"],
                word_data["reading"],
                word_data["definition"]
            )

            picture = None
            image_info = None

            try:
                image_info = images.search_image(
                    example["image_query"]
                )

                if image_info:
                    picture = images.download_image(image_info)

            except (requests.RequestException, ValueError) as error:
                print(f"Image unavailable: {error}")
                image_info = None

            note_id = anki.create_note(
                word_data,
                audio=audio,
                example=example,
                picture=picture,
                image_info=image_info
            )

            existing_words.add(word)
            existing_words.add(word_data["word"])

            created += 1
            print(f"Created: {note_id}")

        except (requests.RequestException, RuntimeError,
                ValueError, KeyError) as error:
            failed += 1
            print(f"Failed: {error}")

    print("\n========== SUMMARY ==========")
    print(f"Total:   {total}")
    print(f"Created: {created}")
    print(f"Skipped: {skipped}")
    print(f"Failed:  {failed}")
    print("=============================")


if __name__ == "__main__":
    main()

