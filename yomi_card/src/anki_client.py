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


    def create_note(self, word_data, audio=None, example=None):
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

        return self.request("addNote", {"note": note})
