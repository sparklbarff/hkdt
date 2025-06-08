diff --git a/README.md b/README.md
index 82e39731d6a4a6e4f64fab269b24705dc2d900ff..d365aad33c41104b3c0f166f800b967a039b6faa 100644
--- a/README.md
+++ b/README.md
@@ -1,99 +1,71 @@
 # hkdt
-Haiku Detector
-Session Reset Prep
-
-I'm continuing work on a Python-based haiku detection script as a final project. The canonical working file is:
-
-/Users/tmbp/haiku_detector/hkdt_v3.py
-
-This script is executed with no arguments. It does not support or expect any command-line flags. All configuration is internal.
-
-File Structure
-
-/Users/tmbp/haiku_detector/
-├── hkdt_v3.py
-├── texts/
-│   └── Author - Title.txt       (downloaded and cleaned)
-└── results/
-└── haiku_zine.md           (formatted output)
-
-Functionality Summary
-
-Downloads the top 100 texts from Project Gutenberg's “Top 100 Yesterday” list
-
-Filters out non-English files using langdetect
-
-Extracts author and title from the Gutenberg header metadata using text.splitlines()
-
-Removes boilerplate content by matching "START OF THE PROJECT GUTENBERG..." and "END OF..."
-
-Files are saved to /texts/ using the cleaned format: Author - Title.txt
-
-Haiku Detection Logic
-
-Uses word-based sliding windows to detect haikus (not line-based)
-
-Target forms: (5, 7, 5) and (3, 5, 3)
-
-Word tokenization via spacy (en_core_web_sm) + sentencizer
-
-Syllables counted using nltk.corpus.cmudict, fallback via regex [aeiouy]+
-
-Lines are filtered to exclude:
-
-numeric-heavy content
 
-all-caps lines
-
-lines with fewer than two words
-
-malformed or fragmentary haikus
-
-Output Format
-
-Output saved to:
-
-/Users/tmbp/haiku_detector/results/haiku_zine.md
-
-Markdown layout:
-
-Section headers: ## Author – Title
-
-Haikus printed as 3 lines + blank line
-
-Each book also saved individually to /results/Author - Title.txt
-
-Example:
+Haiku Detector
 
+This repository contains a Python-based haiku detection script. The canonical file is `hkdt_v3.py` and it runs without command-line arguments. All configuration and paths are internal.
+
+## File Structure
+
+```
+./hkdt_v3.py
+./texts/                 # cleaned downloads
+./results/               # generated haiku files
+    haiku_zine.md
+```
+
+## Process Overview
+1. Download the top 100 texts from [Project Gutenberg's Top 100 Yesterday](https://www.gutenberg.org/browse/scores/top#books-last1).
+2. Filter out non-English files using `langdetect`.
+3. Extract author and title from the Gutenberg header via `text.splitlines()`.
+4. Strip boilerplate text matching "START OF THE PROJECT GUTENBERG" and "END OF" markers.
+5. Convert text to lowercase and remove punctuation, then save as `Author - Title.txt` in `texts/`.
+6. Detect accidental haikus by sliding word windows.
+7. Target forms are 5‑7‑5 and 3‑5‑3 syllable patterns.
+8. Tokenization uses spaCy (`en_core_web_sm`) with a sentencizer.
+9. Syllables are counted with NLTK's `cmudict`, falling back to the regex `[aeiouy]+`.
+10. Lines with numerals or fewer than two words are skipped.
+11. Results are compiled into `results/haiku_zine.md`, grouped under `## Author – Title`. Each haiku is three lines followed by a blank line. Individual results for each book are written to `results/Author - Title.txt`.
+
+### Example
+
+```
 Mary Shelley – Frankenstein
 
 A strange trembling sound
 Rattled the leaves near the tent
 Then it was silent
+```
 
-Runtime Behavior
-
-Uses ThreadPoolExecutor with up to 8 workers to download books in parallel
-
-Uses a deque spinner (|/-\) to simulate a visual scan animation
-
-Deadpan progress messages rotate during processing
-
-Progress is printed inline (no GUI or external logging)
+## Runtime Behavior
+* Uses a `ThreadPoolExecutor` (up to 8 workers) to download books in parallel.
+* Displays a spinner or progress bar during scanning and downloads.
+* Deadpan progress messages rotate while running.
+* Progress is printed inline with no external logging.
 
-Guardrails
+## Guardrails
+* No command-line flags or runtime arguments.
+* No alternative output formats.
+* Avoid large refactors or class-based architectures.
+* Keep the code beginner-friendly.
 
-Do not add flags, dynamic arguments, or alternate output formats
+## Dependencies
 
-Do not reintroduce --verbose, --form, --count
+```bash
+pip install -r requirements.txt
+python3 -m spacy download en_core_web_sm
+python3 -c "import nltk; nltk.download('cmudict')"
+```
 
-No refactors, no functional rearchitecture
+### Running
 
-Code must remain readable and beginner-accessible
+```bash
+python hkdt_v3.py
+```
 
-Dependencies
+Outputs are saved in the `texts/` and `results/` folders.
 
-pip install nltk spacy requests beautifulsoup4 langdetect tqdm
-python3 -m spacy download en_core_web_sm
-python3 -c "import nltk; nltk.download('cmudict')"
+### Testing
 
+```bash
+pytest
+```
