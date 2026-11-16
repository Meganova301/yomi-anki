
import json

from google import genai

from config import GEMINI_MODEL


class SentenceGenerator:

    def __init__(self):
        self.client = genai.Client()

    def generate_example(self, word, reading, definition):
        prompt = f"""
        Create one natural Japanese example sentence.

        Word: {word}
        Reading: {reading}
        Meaning: {definition}

        Requirements:
        - Use the target word naturally and correctly.
        - Use the intended reading and meaning.
        - Aim for JLPT N3-N2 difficulty.
        - Prefer everyday Japanese or natural anime dialogue.
        - Keep the sentence reasonably short.
        - Provide an accurate, natural English translation.
        - Do not include explanations or romaji.


        - Generate a short English image search query.
        - Use 2-5 descriptive words.
        - Describe concrete visual elements from the Japanese sentence.
        - Prefer searchable subjects, actions, places or objects.
        - Avoid abstract words when possible.
        - Do not simply repeat the English translation.
        """

        response = self.client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": {
                    "type": "OBJECT",
                    "properties": {
                        "japanese": {"type": "STRING"},
                        "english": {"type": "STRING"},
                        "image_query": {"type": "STRING"}
                    },
                    "required": ["japanese", "english", "image_query"]
                }
            }
        )

        if not response.text:
            raise ValueError("Gemini returned an empty response.")

        example = json.loads(response.text)

        if not example["japanese"] or not example["english"]:
            raise ValueError("Gemini returned an incomplete example.")
        
        if not example["image_query"].strip():
            raise ValueError("Gemini returned an empty image query.")

        return example
