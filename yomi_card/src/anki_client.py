import requests
from html import escape
from config import ANKI_URL, ANKI_DECK, ANKI_MODEL
from src.http_utils import request_with_retries


_REQUIRED_MODEL_FIELDS = frozenset({
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
})


class AnkiClient:

    def request(self, action, params=None):
        payload = {
            "action": action,
            "version": 6,
            "params": params or {}
        }

        response = request_with_retries(
            requests.post,
            ANKI_URL,
            json=payload,
            timeout=10,
            retry_safe=action in {
                "deckNames",
                "modelNames",
                "modelFieldNames",
                "findNotes",
                "notesInfo",
            },
        )

        data = response.json()

        if data.get("error"):
            raise RuntimeError(data["error"])

        return data["result"]

    def validate_destination(self):
        deck_names = self.request("deckNames")
        if ANKI_DECK not in deck_names:
            raise RuntimeError(
                f"Anki deck '{ANKI_DECK}' was not found. "
                "Create it in Anki or update ANKI_DECK."
            )

        model_names = self.request("modelNames")
        if ANKI_MODEL not in model_names:
            raise RuntimeError(
                f"Anki note type '{ANKI_MODEL}' was not found. "
                "Install it in Anki or update ANKI_MODEL."
            )

        field_names = self.request(
            "modelFieldNames",
            {"modelName": ANKI_MODEL},
        )
        missing_fields = _REQUIRED_MODEL_FIELDS.difference(field_names)
        if missing_fields:
            missing = ", ".join(sorted(missing_fields))
            raise RuntimeError(
                f"Anki note type '{ANKI_MODEL}' is missing required fields: "
                f"{missing}."
            )


    def create_note(
        self,
        word_data,
        example,
        sentence_furigana,
        audio=None,
        picture=None,
        image_info=None,
    ):
        notes = ""
        if image_info:
            source = escape(image_info["source"], quote=True)
            credit = escape(image_info["credit"])
            notes = f'<a href="{source}">{credit}</a>'

        note = {
            "deckName": ANKI_DECK,
            "modelName": ANKI_MODEL,
            "fields": {
                "Word": escape(word_data["word"]),
                "Word Reading": escape(word_data["reading"]),
                "Word Meaning": escape(example["ai_definition"]),
                "Word Furigana": word_data["furigana"],
                "Word Audio": "",
                "Sentence": escape(example["japanese"]),
                "Sentence Meaning": escape(example["english"]),
                "Sentence Furigana": sentence_furigana,
                "Sentence Audio": "",
                "Notes": notes,
                "Pitch Accent": "",
                "Pitch Accent Notes": "",
                "Frequency": word_data["frequency_harmonic_rank"],
                "Picture": "",
            },
            "options": {
                "allowDuplicate": False,
                "duplicateScope": "deck",
            },
            "tags": ["yomicard"],
        }

        if audio:
            note["audio"] = [audio]
        if picture:
            note["picture"] = [picture]

        return self.request("addNote", {"note": note})

    def get_existing_words(self):
        query = f'deck:"{ANKI_DECK}"'
        note_ids = self.request("findNotes", {"query": query})

        existing_words = set()

        for i in range(0, len(note_ids), 100):
            batch = note_ids[i:i + 100]

            notes = self.request(
                "notesInfo",
                {"notes": batch}
            )

            for note in notes:
                fields = note.get("fields", {})
                word = fields.get("Word", {}).get("value", "").strip()

                if not word:
                    word = fields.get("Front", {}).get("value", "").strip()

                if word:
                    existing_words.add(word)

        return existing_words

    def note_exists(self, word, existing_words):
        return word in existing_words

