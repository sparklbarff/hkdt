# hkdt
Haiku Detector
Session Reset Prep

I'm continuing work on a Python-based haiku detection script as a final project. The canonical working file is:

/Users/tmbp/haiku_detector/hkdt_v3.py

This script is executed with no arguments. It does not support or expect any command-line flags. All configuration is internal.

File Structure

/Users/tmbp/haiku_detector/
├── hkdt_v3.py
├── texts/
│   └── Author - Title.txt       (downloaded and cleaned)
└── results/
└── haiku_zine.md           (formatted output)

Functionality Summary

Downloads the top 100 texts from Project Gutenberg's “Top 100 Yesterday” list

Filters out non-English files using langdetect

Extracts author and title from the Gutenberg header metadata using text.splitlines()

Removes boilerplate content by matching "START OF THE PROJECT GUTENBERG..." and "END OF..."

Files are saved to /texts/ using the cleaned format: Author - Title.txt

Haiku Detection Logic

Uses word-based sliding windows to detect haikus (not line-based)

Target forms: (5, 7, 5) and (3, 5, 3)

Word tokenization via spacy (en_core_web_sm) + sentencizer

Syllables counted using nltk.corpus.cmudict, fallback via regex [aeiouy]+

Lines are filtered to exclude:

numeric-heavy content

all-caps lines

lines with fewer than two words

malformed or fragmentary haikus

Output Format

Output saved to:

/Users/tmbp/haiku_detector/results/haiku_zine.md

Markdown layout:

Section headers: ## Author – Title

Haikus printed as 3 lines + blank line

Each book also saved individually to /results/Author - Title.txt

Example:

Mary Shelley – Frankenstein

A strange trembling sound
Rattled the leaves near the tent
Then it was silent

Runtime Behavior

Uses ThreadPoolExecutor with up to 8 workers to download books in parallel

Uses a deque spinner (|/-\) to simulate a visual scan animation

Deadpan progress messages rotate during processing

Progress is printed inline (no GUI or external logging)

Guardrails

Do not add flags, dynamic arguments, or alternate output formats

Do not reintroduce --verbose, --form, --count

No refactors, no functional rearchitecture

Code must remain readable and beginner-accessible

Dependencies

pip install nltk spacy requests beautifulsoup4 langdetect tqdm
python3 -m spacy download en_core_web_sm
python3 -c "import nltk; nltk.download('cmudict')"

