import json

from config import WORDS_FILE
from src.input_manager import read_words
from src.yomitan_client import YomitanClient


def main():
    words = read_words(WORDS_FILE)
    yomitan = YomitanClient()

    for word in words:
        print(f"\nLooking up: {word}")

        result = yomitan.lookup_word(word)
        parsed_entry = yomitan.parse_entry(result)

        print(json.dumps(
            parsed_entry,
            ensure_ascii=False,
            indent=2
        ))


if __name__ == "__main__":
    main()