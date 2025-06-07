#!/usr/bin/env python3
"""
hkdt_v2_syllable_mode.py

Haiku detector that supports:
- Word-by-word sliding window detection
- Line-by-line detection (3 lines with exact syllables)
- Guaranteed 100 English books from Gutenberg Top 200
- Markdown zine output grouped by form (5-7-5 and 3-5-3)
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

def get_metadata(book_id):
    try:
        url = f"https://www.gutenberg.org/ebooks/{book_id}"
        soup = BeautifulSoup(requests.get(url).text, "html.parser")
        title = soup.select_one("meta[name='title']").get("content", "").strip()
        author = soup.select_one("meta[name='author']").get("content", "").strip()
        return f"{author} - {title}".replace("/", "-").replace(":", "").strip()
    except:
        return f"Unknown - {book_id}"

def clean_text(text):
    start = re.search(r"\*\*\* START OF .*? \*\*\*", text)
    end = re.search(r"\*\*\* END OF .*? \*\*\*", text)
    return text[start.end():end.start()].strip() if start and end else text

def download_and_clean(book_id, destination):
    urls = [f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt", f"https://www.gutenberg.org/files/{book_id}/{book_id}.txt"]
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
    soup = BeautifulSoup(requests.get("https://www.gutenberg.org/browse/scores/top").text, "html.parser")
    ebook_ids = [a["href"].split("/")[-1] for a in soup.select("ol:nth-of-type(1) li a[href*='/ebooks/']")[:top_n]]
    downloaded = []
    target_dir.mkdir(parents=True, exist_ok=True)
    for eid in tqdm(ebook_ids, desc="Downloading"):
        result = download_and_clean(eid, target_dir)
        if result: downloaded.append(result)
        if len(downloaded) == required_count:
            break
    return downloaded

def syllable_split(words, targets):
    segments = []
    cursor = 0
    for target in targets:
        line = []
        sc = 0
        while cursor < len(words):
            word = words[cursor]
            sylls = count_syllables(word)
            if sc + sylls > target:
                return None
            line.append(word)
            sc += sylls
            cursor += 1
            if sc == target:
                break
        if sc != target:
            return None
        segments.append(" ".join(line))
    return segments if len(segments) == 3 else None

def find_word_haikus(text, patterns):
    words = word_tokenize(text)
    haikus = {"5-7-5": [], "3-5-3": []}
    for i in range(len(words)):
        chunk = words[i:i+30]
        for pattern in patterns:
            total = sum(pattern)
            count = 0
            for j, w in enumerate(chunk):
                count += count_syllables(w)
                if count == total:
                    window = chunk[:j+1]
                    haiku = syllable_split(window, pattern)
                    if haiku:
                        label = "-".join(map(str, pattern))
                        haikus[label].append(haiku)
                    break
                if count > total:
                    break
    return haikus

def find_line_haikus(text, patterns):
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    haikus = {"5-7-5": [], "3-5-3": []}
    for i in range(len(lines) - 2):
        trio = lines[i:i+3]
        sylls = [sum(count_syllables(w) for w in word_tokenize(line)) for line in trio]
        for pattern in patterns:
            if sylls == pattern:
                label = "-".join(map(str, pattern))
                haikus[label].append(trio)
    return haikus

def extract_haikus(path, mode):
    with open(path, encoding="utf-8", errors="ignore") as f:
        text = clean_text(f.read())
    patterns = [[5, 7, 5], [3, 5, 3]]
    return find_word_haikus(text, patterns) if mode == "word" else find_line_haikus(text, patterns)

def save_results(results, out_md, out_json=None):
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("# Accidental Haikus\n\n")
        for form in ("5-7-5", "3-5-3"):
            f.write(f"## {form} Haikus\n\n")
            for title, found in results.items():
                for h in found.get(form, []):
                    f.write(f"### From *{title}*\n\n" + "\n".join(h) + "\n\n---\n\n")
    if out_json:
        with open(out_json, "w", encoding="utf-8") as jf:
            json.dump(results, jf, indent=2)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--texts", default="/Users/tmbp/haiku_detector/texts", help="Text folder")
    p.add_argument("--output", default="/Users/tmbp/haiku_detector/results/haiku_zine.md", help="Markdown output")
    p.add_argument("--log", default=None, help="Optional JSON debug log")
    p.add_argument("--mode", choices=["line", "word"], default="line", help="Detection mode")
    args = p.parse_args()

    path = Path(args.texts)
    books = fetch_english_texts(path)

    results = {}
    for fname in tqdm(books, desc="Scanning"):
        file_path = path / fname
        haikus = extract_haikus(file_path, args.mode)
        if haikus["5-7-5"] or haikus["3-5-3"]:
            results[fname] = haikus

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    save_results(results, args.output, args.log)
    print(f"✔ Done. Markdown saved to {args.output}")

if __name__ == "__main__":
    main()
