
import json

from google import genai

from config import GEMINI_MODEL

from google.genai.errors import APIError

class SentenceGenerator:

    def __init__(self):
        self.client = genai.Client()

    def generate_example(self, word, reading, dictionary_definition):
        prompt = f"""
        Create a natural Japanese example sentence and a concise English
        definition for the target word.

        Word: {word}
        Reading: {reading}
        Yomitan dictionary sense for context: {dictionary_definition}

        Requirements:
        - Make the English definition concise and specific to the supplied sense.
        - Use the target word naturally and correctly in one short sentence.
        - Provide an accurate, natural English translation.
        - Do not include romaji or explanations.
        - Generate a 2-5 word concrete English image-search query.
        - Do not simply repeat the English translation as the query.
        """

        try:
            response = self.client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": {
                        "type": "OBJECT",
                        "properties": {
                            "ai_definition": {"type": "STRING"},
                            "japanese": {"type": "STRING"},
                            "english": {"type": "STRING"},
                            "image_query": {"type": "STRING"},
                        },
                        "required": [
                            "ai_definition",
                            "japanese",
                            "english",
                            "image_query",
                        ],
                    },
                },
            )
        except APIError as error:
            raise RuntimeError(f"Gemini request failed: {error}") from error

        if not response.text:
            raise ValueError("Gemini returned an empty response.")

        example = json.loads(response.text)
        required_fields = (
            "ai_definition",
            "japanese",
            "english",
            "image_query",
        )
        if not isinstance(example, dict):
            raise ValueError("Gemini returned invalid example data.")

        for field in required_fields:
            value = example.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Gemini returned an invalid {field}.")
            example[field] = value.strip()

        return example
