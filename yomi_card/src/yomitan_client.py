import requests
from html import escape
from src.http_utils import request_with_retries

from config import YOMITAN_URL, YOMITAN_TIMEOUT
class YomitanClient:
    def lookup_word(self, word):
        response = request_with_retries(
            requests.post,
            f"{YOMITAN_URL}/termEntries",
            json={"term": word},
            timeout=YOMITAN_TIMEOUT,
            retry_safe=True,
        )


        return response.json()

    def parse_entry(self, data):
        entries = data.get("dictionaryEntries", [])
        if not entries:
            return None

        entry = next(
            (item for item in entries if item.get("isPrimary")),
            entries[0],
        )
        headwords = entry.get("headwords", [])
        headword = headwords[0] if headwords else {}

        definitions = entry.get("definitions", [])
        definition = next(
            (item for item in definitions if item.get("isPrimary")),
            definitions[0] if definitions else {},
        )
        glosses = self._extract_glossary(definition.get("entries", []))

        headword_index = headword.get("index")
        frequency = next(
            (
                item["frequency"]
                for item in entry.get("frequencies", [])
                if item.get("headwordIndex") == headword_index
                and isinstance(item.get("frequency"), (int, float))
            ),
            None,
        )

        return {
            "word": headword.get("term", ""),
            "reading": headword.get("reading", ""),
            "definition": "; ".join(glosses),
            "frequency": frequency,
        }

    def _extract_glossary(self, node, in_glossary=False):
        if isinstance(node, list):
            return [
                text
                for item in node
                for text in self._extract_glossary(item, in_glossary)
            ]

        if not isinstance(node, dict):
            return []

        data = node.get("data", {})
        in_glossary = in_glossary or (
            isinstance(data, dict) and data.get("content") == "glossary"
        )
        content = node.get("content", [])

        if in_glossary and node.get("tag") == "li":
            text = self._content_text(content).strip()
            return [text] if text else []

        return self._extract_glossary(content, in_glossary)

    def _content_text(self, node):
        if isinstance(node, str):
            return node
        if isinstance(node, list):
            return "".join(self._content_text(item) for item in node)
        if isinstance(node, dict):
            return self._content_text(node.get("content", ""))
        return ""

    def get_sentence_furigana(self, sentence):
        response = request_with_retries(
            requests.post,
            f"{YOMITAN_URL}/tokenize",
            json={"text": sentence, "scanLength": 10},
            timeout=YOMITAN_TIMEOUT,
            retry_safe=True,
        )
        results = response.json()
        if (
            not isinstance(results, list)
            or not results
            or not isinstance(results[0], dict)
        ):
            raise ValueError("Yomitan returned no sentence tokenization.")

        content = results[0].get("content")
        if not isinstance(content, list) or not content:
            raise ValueError("Yomitan returned no sentence tokens.")

        rendered = []
        cursor = 0

        for group in content:
            if not isinstance(group, list) or not group:
                continue

            segment = group[0]
            if not isinstance(segment, dict):
                raise ValueError("Yomitan returned an invalid sentence token.")

            text = segment.get("text")
            reading = segment.get("reading", "")
            if not isinstance(text, str) or not isinstance(reading, str):
                raise ValueError("Yomitan returned an invalid token reading.")
            if not text:
                continue

            position = sentence.find(text, cursor)
            if position == -1:
                raise ValueError(
                    "Yomitan returned token text that does not match the sentence."
                )

            rendered.append(escape(sentence[cursor:position]))

            escaped_text = escape(text)
            if reading and reading != text:
                rendered.append(
                    f"<ruby>{escaped_text}<rt>{escape(reading)}</rt></ruby>"
                )
            else:
                rendered.append(escaped_text)

            cursor = position + len(text)

        rendered.append(escape(sentence[cursor:]))
        return "".join(rendered)

    def get_term_card_data(self, word, reading):
        response = request_with_retries(
            requests.post,
            f"{YOMITAN_URL}/ankiFields",
            json={
                "text": word,
                "type": "term",
                "markers": [
                    "expression",
                    "reading",
                    "audio",
                    "furigana",
                    "frequency-harmonic-rank",
                ],
                "maxEntries": 10,
                "includeMedia": True,
            },
            timeout=YOMITAN_TIMEOUT,
            retry_safe=True,
        )
        data = response.json()

        for field in data.get("fields", []):
            if field.get("expression") != word:
                continue
            if field.get("reading") != reading:
                continue

            furigana = field.get("furigana")
            if not isinstance(furigana, str) or not furigana:
                raise ValueError("Yomitan did not return word furigana.")

            audio_tag = field.get("audio", "")
            for media in data.get("audioMedia", []):
                filename = media.get("ankiFilename")
                if audio_tag != f"[sound:{filename}]" or not media.get("content"):
                    continue

                frequency = field.get("frequency-harmonic-rank")
                return {
                    "audio": {
                        "filename": filename,
                        "data": media["content"],
                        "fields": ["Word Audio"],
                    },
                    "furigana": furigana,
                    "frequency_harmonic_rank": (
                        "" if frequency is None else str(frequency)
                    ),
                }

            return None

        return None