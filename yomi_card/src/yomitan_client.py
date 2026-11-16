import requests

from config import YOMITAN_URL, YOMITAN_TIMEOUT
class YomitanClient:
    def lookup_word(self, word):
        response = requests.post(
            f"{YOMITAN_URL}/termEntries",
            json={"term": word},
            timeout=YOMITAN_TIMEOUT
        )

        response.raise_for_status()

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