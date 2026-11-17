# YomiCard

**Turn Japanese vocabulary into ready-to-study Anki cards.**

YomiCard turns a word list into contextual Japanese flashcards by combining
Yomitan dictionary data and pronunciation audio, Gemini-generated definitions
and example sentences, optional Pixabay images, and AnkiConnect.

Add words to a text file, run the app, and let the pipeline build the cards.

## What it creates

For each new word, YomiCard can add:

- The dictionary form, reading, Yomitan furigana, frequency rank, and
  Yomitan-sourced pronunciation audio.
- A concise, context-aware English definition from Gemini.
- A natural Japanese example sentence and its English translation.
- Sentence furigana from Yomitan. Text not returned by Yomitan's tokenizer is
  preserved as plain text rather than dropped.
- An optional Pixabay image, with attribution in the note.

The configured Anki note type is **Kaishi 1.5k** and the default deck is
**YomiCardV2**. YomiCard checks the deck, note type, and required fields before
processing words.

## How it works

```text
data/words.txt
      |
      v
Read words and check the target Anki deck for duplicates
      |
      v
Yomitan: dictionary entry, reading, frequency, furigana, and audio
      |
      v
Gemini: contextual definition, Japanese sentence, translation, image query
      |
      +----> Yomitan: sentence furigana
      |
      +----> Pixabay: optional image and attribution
      |
      v
AnkiConnect: create the completed note
```

Existing words are skipped before Gemini or Pixabay is called. A failure on one
word is reported without stopping the rest of the batch.

## Requirements

- Python. The current project has been tested with Python 3.14.
- Anki Desktop with the **AnkiConnect** add-on installed and running.
- Yomitan with its local API available.
- A Google Gemini API key.
- A Pixabay API key for image search (optional).

The default local endpoints are:

| Service | Default URL |
| --- | --- |
| Yomitan API | `http://127.0.0.1:19633` |
| AnkiConnect | `http://127.0.0.1:8765` |

## Set up

Run these commands in PowerShell from the project directory:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install requests google-genai
```

Set your API keys in the same PowerShell session. The Gemini SDK reads
`GEMINI_API_KEY`; Pixabay uses `PIXABAY_API_KEY`.

```powershell
$env:GEMINI_API_KEY = "your-gemini-api-key"
$env:PIXABAY_API_KEY = "your-pixabay-api-key"
```

Keep API keys out of source control. Pixabay is optional; if image search is
unavailable, YomiCard reports it and can still create the card without a
picture.

## Configure and run

1. Make sure Anki and Yomitan are running and their local APIs are reachable.
2. In Anki, create the **YomiCardV2** deck and install the **Kaishi 1.5k** note
   type, or update `ANKI_DECK` and `ANKI_MODEL` in `config.py` to match your
   setup.
3. Confirm the note type contains these fields:

   ```text
   Word
   Word Reading
   Word Meaning
   Word Furigana
   Word Audio
   Sentence
   Sentence Meaning
   Sentence Furigana
   Sentence Audio
   Notes
   Pitch Accent
   Pitch Accent Notes
   Frequency
   Picture
   ```

4. Add vocabulary to `data/words.txt`, one word per line:

   ```text
   見逃す
   憧れる
   懐かしい
   ```

5. Run the batch from the project directory:

   ```powershell
   py main.py
   ```

YomiCard validates the Anki destination before processing, then reports
created, skipped, and failed counts when the batch finishes.

## Configuration

Project settings live in `config.py`:

| Setting | Current default | Purpose |
| --- | --- | --- |
| `WORDS_FILE` | `data/words.txt` | Vocabulary input file |
| `YOMITAN_URL` | `http://127.0.0.1:19633` | Yomitan API endpoint |
| `YOMITAN_TIMEOUT` | `10` seconds | Yomitan request timeout |
| `ANKI_URL` | `http://127.0.0.1:8765` | AnkiConnect endpoint |
| `ANKI_DECK` | `YomiCardV2` | Destination deck |
| `ANKI_MODEL` | `Kaishi 1.5k` | Destination note type |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | Sentence-generation model |
| `IMAGE_TIMEOUT` | `10` seconds | Pixabay request timeout |

The Gemini key is read by the Google Gen AI SDK from the environment.
`PIXABAY_API_KEY` is also read from the environment; it is not stored in
`config.py`.

## Reliability and behavior

- **Duplicate-aware:** checks existing notes and words created earlier in the
  same run.
- **Fail-fast setup checks:** a missing deck, note type, or required field is
  reported before expensive generation begins.
- **Per-word recovery:** lookup or generation errors are reported, and later
  words continue processing.
- **Bounded retries:** retry-safe HTTP requests handle selected transient
  failures; Anki note creation is not automatically retried.
- **Optional images:** a missing Pixabay key, no matching image, or image
  request failure does not prevent a card from being created.
- **Yomitan audio:** pronunciation audio comes from Yomitan; words without
  matching audio are skipped.

## Product roadmap

These are planned improvements, not shipped features:

- **Smarter image matching:** try alternate search phrases from the same
  generation request, compare Pixabay result tags, and omit weak matches rather
  than compromise sentence quality or attach an irrelevant image.
- **Japanese sentence playback:** add locally generated speech to the existing
  `Sentence Audio` field while keeping Yomitan as the source of word audio;
  select voices with licensing and attribution requirements in mind.
- **Card quality guardrails:** verify the example uses the target word, flag
  sentence text that lacks furigana, and offer a preview before adding a note.
- **Portfolio-grade repeatability:** make dependency setup reproducible, run the
  test suite automatically in CI, and report useful per-run timing and failure
  metrics.

## Run the tests

From the project directory:

```powershell
py -m unittest discover -s tests -v
```

The unit tests use mocks for external services, so they do not require live
Anki, Yomitan, Gemini, or Pixabay connections.

## Project layout

```text
yomi_card/
├── config.py
├── main.py
├── data/
│   └── words.txt
├── src/
│   ├── anki_client.py
│   ├── http_utils.py
│   ├── image_provider.py
│   ├── input_manager.py
│   ├── sentence_generator.py
│   └── yomitan_client.py
└── tests/
    ├── test_anki_client.py
    ├── test_http_utils.py
    ├── test_image_provider.py
    ├── test_main.py
    ├── test_sentence_generator.py
    └── test_yomitan_client.py
```
