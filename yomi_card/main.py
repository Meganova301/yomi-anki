from config import WORDS_FILE
from src.input_manager import read_words
from src.yomitan_client import YomitanClient


def main():
    words = read_words(WORDS_FILE)

    yomitan = YomitanClient()

    for word in words:
        print(f"Looking up: {word}")

        result = yomitan.lookup_word(word)

        print(result)
        print()


if __name__ == "__main__":
    main()