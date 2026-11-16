import unittest

from src.yomitan_client import YomitanClient


class TestYomitanClient(unittest.TestCase):

    def setUp(self):
        self.client = YomitanClient()

    def test_empty_entries(self):
        result = self.client.parse_entry({"dictionaryEntries": []})
        self.assertIsNone(result)

    def test_missing_headwords(self):
        data = {
            "dictionaryEntries": [
                {"headwords": [], "definitions": []}
            ]
        }

        result = self.client.parse_entry(data)
        self.assertEqual(result["word"], "")
        self.assertEqual(result["reading"], "")
        self.assertEqual(result["definition"], "")
        self.assertIsNone(result["frequency"])


if __name__ == "__main__":
    unittest.main()