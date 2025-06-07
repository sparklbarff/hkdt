
#!/usr/bin/env python3
"""
hkdt_v2_final_metadata_fix.py — Accidental Haiku Detector (Final Fix)
"""

import re
import argparse
import requests
import json
import random
from langdetect import detect, DetectorFactory
from pathlib import Path
from bs4 import BeautifulSoup
from nltk.tokenize import word_tokenize
from nltk.corpus import cmudict
from tqdm import tqdm
import nltk

DetectorFactory.seed = 0
nltk.download("punkt")
nltk.download("cmudict")
cmu_dict = cmudict.dict()

deadpan_lines = [
    "Waiting for something vaguely syllabic to happen",
    "Scraping 19th-century sentence mush for elegance",
    "Counting syllables like it means something",
    "Hoping the public domain doesn't disappoint again",
    "Running from prose like it owes us money",
    "Sorting the nonsense into structured nonsense",
    "Staring into the lexical abyss (it's staring back)",
    "Doing unspeakable things to the English canon",
    "Giving syllables the side-eye"
]

def count_syllables(word):
    word = word.lower()
    if word in cmu_dict:
        return min(len([ph for ph in pron if ph[-1].isdigit()]) for pron in cmu_dict[word])
    return len(re.findall(r"[aeiouy]+", word))

def get_metadata(book_id):
    try:
        url = f"https://www.gutenberg.org/ebooks/{book_id}"
        soup = BeautifulSoup(requests.get(url).text, "html.parser")
        title = soup.select_one("meta[name='title']").get("content", "").strip()
        author = soup.select_one("meta[name='author']").get("content", "").strip()
        return author, title
    except:
        return "Unknown", str(book_id)

def clean_text(text):
    start = re.search(r"\*\*\* START OF .*? \*\*\*", text)
    end = re.search(r"\*\*\* END OF .*? \*\*\*", text)
    return text[start.end():end.start()].strip() if start and end else text

def download_and_clean(book_id, destination, meta_map):
    urls = [f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt",
            f"https://www.gutenberg.org/files/{book_id}/{book_id}.txt"]
    for url in urls:
        try:
            r = requests.get(url, timeout=10)
            if r.ok and len(r.text) > 1000:
                text = clean_text(r.text)
                snippet = text[:1500]
                if detect(snippet) != "en":
                    return None
                author, title = get_metadata(book_id)
                filename = f"{author} - {title}".replace("/", "-").replace(":", "").strip() + ".txt"
                meta_map[filename] = (author, title)
                with open(destination / filename, "w", encoding="utf-8") as f:
                    f.write(text)
                return filename
        except:
            continue
    return None

def fetch_english_texts(path, target=100, top_n=200):
    soup = BeautifulSoup(requests.get("https://www.gutenberg.org/browse/scores/top").text, "html.parser")
    ebook_ids = [a["href"].split("/")[-1] for a in soup.select("ol:nth-of-type(1) li a[href*='/ebooks/']")[:top_n]]
    path.mkdir(parents=True, exist_ok=True)
    downloaded = []
    meta_map = {}
    for eid in tqdm(ebook_ids, desc="Fetching from Gutenberg"):
        file = download_and_clean(eid, path, meta_map)
        if file:
            downloaded.append(file)
        if len(downloaded) == target:
            break
    return downloaded, meta_map

def is_clean_line(line):
    if not line or line.strip() == "":
        return False
    if len(line.split()) < 2:
        return False
    if any(char.isdigit() for char in line):
        return False
    if line.isupper():
        return False
    if not re.match(r"^[A-Z]", line):
        return False
    return True

def syllable_split(words, pattern):
    lines, cursor = [], 0
    for target in pattern:
        line, count = [], 0
        while cursor < len(words):
            word = words[cursor]
            sc = count_syllables(word)
            if count + sc > target:
                return None
            line.append(word)
            count += sc
            cursor += 1
            if count == target:
                break
        if count != target:
            return None
        composed = " ".join(line).strip()
        if not is_clean_line(composed):
            return None
        lines.append(composed)
    return lines

def detect_haikus(text, patterns, verbose=False):
    words = word_tokenize(text)
    haikus = { "5-7-5": [], "3-5-3": [] }
    for i in range(len(words)):
        chunk = words[i:i+30]
        for pattern in patterns:
            total = sum(pattern)
            count, j = 0, 0
            while j < len(chunk):
                count += count_syllables(chunk[j])
                if count == total:
                    split = syllable_split(chunk[:j+1], pattern)
                    if split:
                        form = "-".join(map(str, pattern))
                        haikus[form].append(split)
                        if verbose:
                            print(f"
{form} Haiku Found:
" + "
".join(split) + "
" + "-"*30)
                    break
                elif count > total:
                    break
                j += 1
    return haikus

def extract_haikus(file_path, verbose=False):
    with open(file_path, encoding="utf-8", errors="ignore") as f:
        text = f.read()
    text = clean_text(text)
    return detect_haikus(text, [[5,7,5], [3,5,3]], verbose=verbose)

def save_results(results, meta, out_md, out_json=None):
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("# Accidental Haikus\n\n")
        for form in ("5-7-5", "3-5-3"):
            f.write(f"## {form} Haikus\n\n")
            for filename, entries in results.items():
                author, title = meta.get(filename, ("Unknown", filename.replace(".txt", "")))
                header = f"** From _{title}_ by {author} ** [{form}]"
                for haiku in entries.get(form, []):
                    f.write(f"{header}\n\n")
                    for line in haiku:
                        f.write(f"    {line}\n")
                    f.write("\n---\n\n")
    if out_json:
        with open(out_json, "w", encoding="utf-8") as j:
            json.dump(results, j, indent=2)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--texts", default="texts", help="Text folder")
    parser.add_argument("--output", default="results/haiku_zine.md", help="Markdown output")
    parser.add_argument("--log", default=None, help="Optional JSON debug log")
    parser.add_argument("--verbose", action="store_true", help="Print haikus live")
    args = parser.parse_args()

    books, meta = fetch_english_texts(Path(args.texts))
    desc = random.choice(deadpan_lines)
    results = {}
    for fname in tqdm(books, desc=desc):
        path = Path(args.texts) / fname
        haikus = extract_haikus(path, verbose=args.verbose)
        if haikus["5-7-5"] or haikus["3-5-3"]:
            results[fname] = haikus

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    save_results(results, meta, args.output, args.log)
    print(f"✅ Haiku zine saved to {args.output}")

if __name__ == "__main__":
    main()
