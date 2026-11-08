def read_words(file_path):
    words = []

    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            word = line.strip()

            if word:
                words.append(word)

    return words

