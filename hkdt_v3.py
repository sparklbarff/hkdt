import re
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import sys
import random
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed

import nltk
import spacy
from langdetect import detect, LangDetectException
from nltk.corpus import cmudict
from tqdm import tqdm

# Initialize resources
nltk.download("cmudict", quiet=True)
syllable_dict = cmudict.dict()
# Load spaCy small model with sentencizer
nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
nlp.max_length = 5_000_000  # allow longer texts
nlp.add_pipe("sentencizer")

# Paths & URLs
BASE_DIR = Path(__file__).parent
TEXT_DIR = BASE_DIR / "texts"
RESULT_DIR = BASE_DIR / "results"
ZINE_FILE = RESULT_DIR / "haiku_zine.md"
TOP_URL = "https://www.gutenberg.org/browse/scores/top"

# Spinner and messages
spinner = deque('|/-\\')
deadpan_lines = [
    "Assessing literary potential…",
    "Counting syllables with stoic precision…",
    "Scanning the classics for accidental poetry…",
    "Polishing haiku gems…",
]

def spin(msg: str):
    spinner.rotate(1)
    sys.stdout.write(f"\r{spinner[0]} {msg}")
    sys.stdout.flush()

# Limits
MAX_BOOKS = 100
TARGET_HAIKU_COUNT = 100

# Ensure directories exist
TEXT_DIR.mkdir(parents=True, exist_ok=True)
RESULT_DIR.mkdir(parents=True, exist_ok=True)

# Utilities
def clean_filename(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9 _\-\.]", "", name).strip()


def simple_clean(text: str) -> str:
    """Lowercase and remove punctuation from text, collapsing extra spaces."""
    lines = []
    for ln in text.splitlines():
        cleaned = re.sub(r"[^a-z ]+", "", ln.lower())
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if cleaned:
            lines.append(cleaned)
    return "\n".join(lines)


def count_syllables(word: str) -> int:
    w = word.lower()
    if w in syllable_dict:
        return min(len([s for s in pron if s[-1].isdigit()]) for pron in syllable_dict[w])
    return len(re.findall(r"[aeiouy]+", w)) or 1


def is_valid_line(words: list[str]) -> bool:
    if len(words) < 2:
        return False
    if any(char.isdigit() for w in words for char in w):
        return False
    line = " ".join(words)
    return len(line) >= 5


def sliding_windows(words: list[str], sizes: tuple[int, ...]):
    total = sum(sizes)
    for i in range(len(words) - total + 1):
        segments, cursor = [], i
        for sz in sizes:
            chunk, count = [], 0
            while cursor < len(words) and count + count_syllables(words[cursor]) <= sz:
                chunk.append(words[cursor])
                count += count_syllables(words[cursor])
                cursor += 1
            if count != sz:
                break
            segments.append(chunk)
        if len(segments) == len(sizes) and all(is_valid_line(seg) for seg in segments):
            yield [" ".join(seg) for seg in segments]

# Download helper
def download_text(link) -> Path | None:
    href = link.get('href', '')
    if not href.startswith('/ebooks/'):
        return None
    book_id = href.rsplit('/', 1)[-1]
    for suffix in ('-0.txt', '.txt'):
        url = f"https://www.gutenberg.org/files/{book_id}/{book_id}{suffix}"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code != 200 or not r.text:
                continue
            snippet = r.text[:2000]
            try:
                if detect(snippet) != 'en':
                    return None
            except LangDetectException:
                return None
            lines = r.text.splitlines()
            body, main = [], False
            for ln in lines:
                low = ln.strip().lower()
                if 'start of the project gutenberg' in low:
                    main = True
                    continue
                if 'end of the project gutenberg' in low:
                    break
                if main:
                    body.append(ln)
            clean_text = simple_clean("\n".join(body))
            if not clean_text.strip():
                return None
            header = lines[:200]
            author = next((line.split(':',1)[1].strip() for line in header if line.lower().startswith('author:')), 'Unknown')
            raw = link.text.strip()
            title, _, _ = raw.partition(' by ')
            fname = clean_filename(f"{author} - {title}.txt")
            out = TEXT_DIR / fname
            out.write_text(clean_text, encoding='utf-8')
            return out
        except:
            continue
    return None

# Fetch top texts
def fetch_top_texts():
    print('📕 Starting Gutenberg download…')
    r = requests.get(TOP_URL, timeout=10)
    soup = BeautifulSoup(r.text, 'html.parser')
    headers = [h for h in soup.find_all('h2') if 'Top 100 EBooks' in h.text]
    links = []
    for hdr in headers[:2]:
        ol = hdr.find_next_sibling('ol')
        if ol:
            links.extend(ol.find_all('a', href=True))
    saved = 0
    desc = random.choice(deadpan_lines)
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = [ex.submit(download_text, lk) for lk in links[:MAX_BOOKS]]
        for fut in tqdm(as_completed(futures), total=len(futures), desc=desc, leave=False):
            spin(desc)
            path = fut.result()
            if path:
                saved += 1
            if saved >= TARGET_HAIKU_COUNT:
                break
    sys.stdout.write('\n')
    print(f"✅ Completed downloads: {saved} texts saved to {TEXT_DIR}")

# Scan helper
def scan_file(path: Path) -> list[list[str]]:
    text = path.read_text(errors='ignore')
    try:
        if detect(text[:2000]) != 'en':
            return []
    except:
        return []
    lines = text.splitlines()
    body, main = [], False
    for ln in lines:
        low = ln.strip().lower()
        if 'start of the project gutenberg' in low:
            main = True
            continue
        if 'end of the project gutenberg' in low:
            break
        if main:
            body.append(ln)
    if not body:
        body = lines
    clean_text = simple_clean("\n".join(body))
    found = set()
    for sent in tqdm(nlp(clean_text).sents, desc='Scanning', leave=False):
        spin("Scanning text…")
        words = [w.text for w in sent if w.is_alpha]
        for form in ((5,7,5),(3,5,3)):
            for h in sliding_windows(words, form):
                found.add(tuple(h))
    return [list(h) for h in found]

# Main
def main():
    fetch_top_texts()
    files = list(TEXT_DIR.glob('*.txt'))[:MAX_BOOKS]
    print(f'⚙️ Scanning {len(files)} text files for haikus…')
    total, zine = 0, ['# Accidental Haikus\n']
    for fpath in files:
        spin("Processing file…")
        haikus = scan_file(fpath)
        if not haikus:
            continue
        author, title = fpath.stem.split(' - ',1)
        out_book = RESULT_DIR / fpath.name
        with out_book.open('w', encoding='utf-8') as ob:
            for h in haikus:
                ob.write("\n".join(h)+"\n\n")
        zine.append(f"## {author} – {title}\n")
        for h in haikus:
            zine.append("\n".join(h)+"\n")
        zine.append("\n")
        total += 1
        if total >= TARGET_HAIKU_COUNT:
            break
    ZINE_FILE.write_text(''.join(zine), encoding='utf-8')
    print(f"\nScan complete. {total} sources processed.")

if __name__ == '__main__':
    main()
