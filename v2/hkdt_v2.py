#!/usr/bin/env python3
"""
hkdt_v2.py — Accidental Haiku Extractor

- Downloads top 200 Gutenberg books
- Filters for 100 valid English `.txt` files with clean metadata
- Detects both 5-7-5 and 3-5-3 haikus
- Validates strict 3-line structure
- Groups haikus by form in Markdown output
- Optionally writes JSON debug logs
"""

import re
import argparse
import requests
import json
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

def count_syllables(word):
    word = word.lower()
    if word in cmu_dict:
        return min(len([ph for ph in pron if ph[-1].isdigit()]) for pron in cmu_dict[word])
    return len(re.findall(r"[aeiouy]+", word))

def line_syllable_count(line):
    return sum(count_syllables(w) for w in word_tokenize(line) if w.isalpha())

def is_haiku(lines, pattern):
    if len(lines) != 3: return False
    if any(len(word_tokenize(line)) < 2 for line in lines): return False
    return all(line_syllable_count(line) == count for line, count in zip(lines, pattern))

def get_metadata(book_id):
    url = f"https://www.gutenberg.org/ebooks/{book_id}"
    r = requests.get(url, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")
    try:
        title = soup.select_one("meta[name='title']").get("content", "").strip()
        author = soup.select_one("meta[name='author']").get("content", "").strip()
    except:
        title, author = str(book_id), "Unknown"
    filename = f"{author} - {title}".replace("/", "-").replace(":", "").strip()
    return filename or str(book_id)

def clean_text(text):
    start = re.search(r"\*\*\* START OF .*? \*\*\*", text)
    end = re.search(r"\*\*\* END OF .*? \*\*\*", text)
    return text[start.end():end.start()].strip() if start and end else text

def download_and_clean(book_id, destination):
    urls = [
        f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt",
        f"https://www.gutenberg.org/files/{book_id}/{book_id}.txt"
    ]
    for url in urls:
        try:
            r = requests.get(url, timeout=10)
            if r.ok and len(r.text) > 1000:
                snippet = clean_text(r.text[:1500])
                if detect(snippet) != "en":
                    return None
                name = get_metadata(book_id) + ".txt"
                with open(destination / name, "w", encoding="utf-8") as f:
                    f.write(r.text)
                return name
        except:
            continue
    return None

def fetch_english_texts(target_dir, required_count=100, top_n=200):
    url = "https://www.gutenberg.org/browse/scores/top"
    soup = BeautifulSoup(requests.get(url).text, "html.parser")
    ebook_ids = [a["href"].split("/")[-1] for a in soup.select("ol:nth-of-type(1) li a[href*='/ebooks/']")[:top_n]]

    downloaded = []
    target_dir.mkdir(parents=True, exist_ok=True)
    for eid in tqdm(ebook_ids, desc="Downloading"):
        result = download_and_clean(eid, target_dir)
        if result: downloaded.append(result)
        if len(downloaded) == required_count:
            break
    return downloaded

def extract_haikus_from_file(path):
    with open(path, encoding="utf-8", errors="ignore") as f:
        raw = clean_text(f.read())
    blocks = [b.strip() for b in raw.split("\n\n") if b.count("\n") >= 2]
    haikus = {"5-7-5": [], "3-5-3": []}
    for block in blocks:
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        if len(lines) >= 3:
            trio = lines[:3]
            if is_haiku(trio, [5, 7, 5]):
                haikus["5-7-5"].append(trio)
            elif is_haiku(trio, [3, 5, 3]):
                haikus["3-5-3"].append(trio)
    return haikus

def save_results(results, out_md, out_json=None):
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("# Accidental Haikus\n\n")
        for form in ("5-7-5", "3-5-3"):
            f.write(f"## {form} Haikus\n\n")
            for title, haikus in results.items():
                for h in haikus[form]:
                    f.write(f"### From *{title}*\n\n")
                    f.write("\n".join(h) + "\n\n---\n\n")
    if out_json:
        with open(out_json, "w", encoding="utf-8") as jf:
            json.dump(results, jf, indent=2)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--texts", default="/Users/tmbp/haiku_detector/texts", help="Download directory")
    parser.add_argument("--output", default="/Users/tmbp/haiku_detector/results/haiku_zine.md", help="Zine path")
    parser.add_argument("--log", default=None, help="Optional JSON debug log")
    args = parser.parse_args()

    path = Path(args.texts)
    books = fetch_english_texts(path)

    results = {}
    for fname in tqdm(books, desc="Scanning"):
        full_path = path / fname
        haikus = extract_haikus_from_file(full_path)
        if haikus["5-7-5"] or haikus["3-5-3"]:
            results[fname] = haikus

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    save_results(results, args.output, out_json=args.log)
    print(f"✔ Finished. Markdown saved to {args.output}")

if __name__ == "__main__":
    main()
