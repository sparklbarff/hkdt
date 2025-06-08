# hkdt

Haiku Detector

This repository contains a Python-based haiku detection script. The canonical file is `hkdt_v3.py` and it runs without command-line arguments. All configuration and paths are internal.

## File Structure

```
./hkdt_v3.py
./texts/                 # cleaned downloads
./results/               # generated haiku files
    haiku_zine.md
```

## Process Overview
1. Download the top 100 texts from [Project Gutenberg's Top 100 Yesterday](https://www.gutenberg.org/browse/scores/top#books-last1).
2. Filter out non-English files using `langdetect`.
3. Extract author and title from the Gutenberg header via `text.splitlines()`.
4. Strip boilerplate text matching "START OF THE PROJECT GUTENBERG" and "END OF" markers.
5. Save cleaned text as `Author - Title.txt` in `texts/`.
6. Detect accidental haikus by sliding word windows.
7. Target forms are 5‑7‑5 and 3‑5‑3 syllable patterns.
8. Tokenization uses spaCy (`en_core_web_sm`) with a sentencizer.
9. Syllables are counted with NLTK's `cmudict`, falling back to the regex `[aeiouy]+`.
10. Lines with heavy numerals, all caps, fewer than two words, or otherwise fragmentary are skipped.
11. Results are compiled into `results/haiku_zine.md`, grouped under `## Author – Title`. Each haiku is three lines followed by a blank line. Individual results for each book are written to `results/Author - Title.txt`.

### Example

```
Mary Shelley – Frankenstein

A strange trembling sound
Rattled the leaves near the tent
Then it was silent
```

## Runtime Behavior
* Uses a `ThreadPoolExecutor` (up to 8 workers) to download books in parallel.
* Displays a spinner or progress bar during scanning and downloads.
* Deadpan progress messages rotate while running.
* Progress is printed inline with no external logging.

## Guardrails
* No command-line flags or runtime arguments.
* No alternative output formats.
* Avoid large refactors or class-based architectures.
* Keep the code beginner-friendly.

## Dependencies

```
pip install nltk spacy requests beautifulsoup4 langdetect tqdm
python3 -m spacy download en_core_web_sm
python3 -c "import nltk; nltk.download('cmudict')"
```
