Session Reset Prep

I'm continuing work on a Python-based haiku detection script as a final project. The canonical working file is:

/Users/tmbp/haiku\_detector/hkdt\_v3.py

This script is executed with no arguments. It does not support or expect any command-line flags. All configuration is internal.

The script detects accidental/unintentional haikus in public domain text using word-based syllable scanning.

File Structure:

/Users/tmbp/haiku\_detector/
├── hkdt\_v3.py
├── texts/
│   └── Author - Title.txt       (downloaded and cleaned)
└── results/
└── haiku\_zine.md           (formatted output)

Process Overview:

1. Download top 100 texts from yesterday from Gutenberg
   [https://www.gutenberg.org/browse/scores/top#books-last1](https://www.gutenberg.org/browse/scores/top#books-last1)

2. Clean and prepare each file by removing Gutenberg header/footer and other extraneous text. Save cleaned files into /texts/.

3. Detect haikus using a sliding word window. Each detection must contain exactly 17 syllables (for 5-7-5) or 11 syllables (for 3-5-3). Punctuation and sentence boundaries are respected.

4. Write results in Markdown format to /results/haiku\_zine.md with readable formatting.

5. Use visually appealing and, if possible, animated progress meters to track download and scanning sections.

Functionality Summary:

* Filters out non-English files using langdetect
* Extracts author and title using text.splitlines()
* Removes boilerplate content using regex matches on START OF THE PROJECT GUTENBERG... and END OF...
* Files are saved in /texts/ using the format Author - Title.txt

Haiku Detection Logic:

* Sliding word-window scanning strategy
* Detects 5-7-5 and 3-5-3 syllable patterns only
* Syllables counted using nltk.corpus.cmudict, with regex fallback \[aeiouy]+
* Tokenization is handled by spacy with en\_core\_web\_sm and a sentencizer
* Lines rejected if:

  * Numeric-heavy
  * All caps
  * Too short (less than 2 words)
  * Does not start with capital letter
  * Fragmentary or non-linguistic

Output Format:

Output saved to:
/Users/tmbp/haiku\_detector/results/haiku\_zine.md

* Markdown format
* Grouped by Author – Title
* Each haiku printed as 3 lines with a blank line and a horizontal divider

Example:

Mary Shelley - Frankenstein

A strange trembling sound
Rattled the leaves near the tent
Then it was silent

---

Runtime Behavior:

* Uses ThreadPoolExecutor with up to 8 workers to parallelize download
* Displays animated progress bar using tqdm or custom spinner for scanning
* Randomized deadpan progress messages replace traditional labels

Guardrails:

* No command-line flags or runtime arguments
* No alternate output formats
* No class-based refactor
* Keep code readable and inline with Python beginner-level conventions

Dependencies:

pip install nltk spacy requests beautifulsoup4 langdetect tqdm
python3 -m spacy download en\_core\_web\_sm
python3 -c "import nltk; nltk.download('cmudict')"
