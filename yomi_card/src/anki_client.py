import requests

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

    def create_note(self, word_data):
        word = word_data["word"]
        reading = word_data["reading"]
        definition = word_data["definition"]
        frequency = word_data["frequency"]

        back = f"{reading}<hr>{definition}"

        if frequency is not None:
            back += f"<br>Frequency: {frequency}"

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

        return self.request("addNote", {"note": note})