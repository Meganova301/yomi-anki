import requests
from html import escape
from config import ANKI_URL, ANKI_DECK, ANKI_MODEL


class AnkiClient:

    def request(self, action, params=None):
        payload = {
            "action": action,
            "version": 6,
            "params": params or {}
        }

        response = requests.post(
            ANKI_URL,
            json=payload,
            timeout=10
        )

        response.raise_for_status()
        data = response.json()

        if data.get("error"):
            raise RuntimeError(data["error"])

        return data["result"]


    def create_note(self, word_data, audio=None, example=None, picture=None, image_info=None):
        word = escape(word_data["word"])
        reading = escape(word_data["reading"])
        definition = escape(word_data["definition"])
        frequency = word_data["frequency"]

        back = f"{reading}<hr>{definition}"

        if frequency is not None:
            back += f"<br>Frequency: {frequency}"

        if example:
            japanese = escape(example["japanese"])
            english = escape(example["english"])

            back += (
                f"<hr>{japanese}"
                f"<br>{english}"
            )

        if image_info:
            credit = escape(image_info["credit"])
            source = escape(image_info["source"], quote=True)

            back += (
                f'<br><small>'
                f'<a href="{source}">{credit}</a>'
                f'</small>'
            )
        note = {
            "deckName": ANKI_DECK,
            "modelName": ANKI_MODEL,
            "fields": {
                "Front": word,
                "Back": back
            },
            "options": {
                "allowDuplicate": False,
                "duplicateScope": "deck"
            },
            "tags": ["yomicard"]
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
                front = note.get("fields", {}).get("Front", {})
                word = front.get("value", "").strip()

                if word:
                    existing_words.add(word)

        return existing_words

    def note_exists(self, word, existing_words):
        return word in existing_words

