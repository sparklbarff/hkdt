hkdt - Accidental Haiku Detector

Purpose:
A self‑contained, beginner‑accessible Python script (hkdt\_v3.py) that automatically:

* Downloads the top 100 titles from Project Gutenberg’s “Top 100 Yesterday” list.
* Cleans each text, removes Gutenberg boilerplate, normalises punctuation, and stores the result as "Author - Title.txt" in the texts/ directory.
* Scans every cleaned file for accidental haikus in both 5‑7‑5 (17‑syllable) and 3‑5‑3 (11‑syllable) forms using a sliding‑window syllable counter.
* Collects validated haikus, groups them by source, and publishes them to results/haiku\_zine.md and to individual per‑book files.

Installation:

1. Clone the repository.
2. (Optional) create and activate a virtual environment.
3. pip install -r requirements.txt
4. python -m spacy download en\_core\_web\_sm
5. python -c "import nltk, sys; nltk.download('cmudict')"

Running:
python hkdt\_v3.py
All progress appears inline: a spinner or progress bar with rotating deadpan messages. Download and scan phases run in parallel using a ThreadPoolExecutor set to eight workers. Upon completion the script prints a summary and exits.

Workflow Details:
Download Phase:

* Scrape the Gutenberg index page.
* Fetch plain‑text UTF‑8 files; retry on transient errors with exponential back‑off.

Cleaning Phase:

* Locate "\*\*\* START OF THE PROJECT GUTENBERG" and "\*\*\* END" markers; discard text outside these boundaries.
* Convert CRLF or CR line endings to LF.
* Convert to lowercase and strip punctuation (apostrophes retained).
* Extract Title: and Author: headers; default to "Unknown" if absent.
* Save to texts/ using the format Author - Title.txt.

Tokenisation and Syllable Counting:

* spaCy (en\_core\_web\_sm) provides sentence and token boundaries.
* NLTK cmudict gives primary syllable counts; missing words fall back to a regex heuristic: \[aeiouy]+.
* Tokens containing numerals or with fewer than two alphabetic characters are ignored.

Sliding‑Window Haiku Detection:

* Window sizes of 17 and 11 words slide through each sentence‑sequence.
* For each window the total syllable count must equal 17 or 11.
* The algorithm iterates over possible split points to achieve 5‑7‑5 or 3‑5‑3.
* Reject windows with all‑caps words, digits, or any line having fewer than two words.
* Store unique haikus only; duplicates are discarded.

Output Assembly:

* Write each book’s haikus to results/Author - Title.txt.
* Build haiku\_zine.md: an index showing book counts, followed by "## Author - Title" headers and the book’s haikus (three lines plus blank line).

Runtime Behaviour:

* Eight download threads (constant MAX\_WORKERS) running via ThreadPoolExecutor.
* Animated spinner (| / - ) or tqdm progress bar during long operations.
* No GUI, no external logging; console output only when necessary.

Guardrails:

* No command‑line switches, dynamic arguments, or alternative output formats.
* No refactors introducing class hierarchies or configuration files.
* Code remains readable for beginners; imperative style only.
* Project adheres to internal "no em dash" policy; plain hyphens or en‑dashes allowed.

Dependencies:

* requests
* beautifulsoup4
* spacy >= 3.7
* nltk
* tqdm
* langdetect

Testing:
pytest discovers the unit tests located beside hkdt\_v3.py.

Extending the Script (quick hints):

* Add new haiku forms: edit the TARGET\_PATTERNS list.
* Change thread count: edit MAX\_WORKERS.
* Skip downloads when books already exist: set SKIP\_DOWNLOAD = True.
* Enable optional JSON debug logging: uncomment DEBUG\_JSON = True in the script.

Contributing Guidelines:

* Open an issue before submitting pull requests.
* Follow the no‑flag, no‑em‑dash rule.
* Include unit tests and run pre‑commit formatting hooks.
  \\
