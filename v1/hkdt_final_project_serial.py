#!/usr/bin/env python3
"""
Haiku Detector – Final Project (Robust Version)

- Downloads the top 100 texts from Project Gutenberg
- Filters non-English content using langdetect
- Detects both 5-7-5 and 3-5-3 haikus
- Validates strict 3-line structure and filters malformed lines
- Outputs clean Markdown zine
"""

import re
import argparse
import requests
from langdetect import detect
from langdetect import DetectorFactory
DetectorFactory.seed = 0  # Ensures consistent detection and prevents race conditions
from pathlib import Path
from bs4 import BeautifulSoup
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import cmudict
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import nltk

nltk.download("punkt")
nltk.download("cmudict")

cmu_dict = cmudict.dict()

def count_syllables(word):
    word = word.lower()
    if word in cmu_dict:
        return min(len([ph for ph in pron if ph[-1].isdigit()]) for pron in cmu_dict[word])
    return len(re.findall(r"[aeiouy]+", word))

def line_syllable_count(line):
    words = word_tokenize(line)
    return sum(count_syllables(w) for w in words if w.isalpha())

def is_clean_haiku(trio, pattern):
    if len(trio) != 3:
        return False
    if any(len(word_tokenize(line)) < 2 for line in trio):
        return False
    if any(re.match(r"^[A-Z]\.$", w.strip()) for line in trio for w in line.split()):
        return False
    return all(line_syllable_count(line) == target for line, target in zip(trio, pattern))

def detect_haikus(text, patterns):
    sents = sent_tokenize(text)
    return [
        trio for i in range(len(sents)-2)
        for pattern in patterns
        if is_clean_haiku(sents[i:i+3], pattern)
    ]

def clean_gutenberg_text(text):
    start = re.search(r"\*\*\* START OF .*? \*\*\*", text)
    end = re.search(r"\*\*\* END OF .*? \*\*\*", text)
    if start and end:
        return text[start.end():end.start()].strip()
    return text

def get_metadata(book_id):
    url = f"https://www.gutenberg.org/ebooks/{book_id}"
    r = requests.get(url, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")
    try:
        title = soup.select_one("meta[name='title']") or soup.select_one("h1")
        title = title["content"] if title.name == "meta" else title.get_text(strip=True)
        author_tag = soup.select_one("meta[name='author']") or soup.select_one("h2")
        author = author_tag["content"] if author_tag and author_tag.name == "meta" else author_tag.get_text(strip=True)
    except:
        title, author = book_id, "Unknown"
    filename = f"{author} - {title}".replace(":", "").replace("/", "-").replace("\\", "-").strip()
    return filename

def try_download(eid, destination):
    urls = [
        f"https://www.gutenberg.org/files/{eid}/{eid}-0.txt",
        f"https://www.gutenberg.org/files/{eid}/{eid}.txt"
    ]
    for url in urls:
        try:
            r = requests.get(url, timeout=10)
            if r.ok and len(r.text) > 1000:
                clean_text = clean_gutenberg_text(r.text)
                try:
                    lang = detect(clean_text[:1000])
                    if lang != "en":
                        return None
                except:
                    return None
                    return None
                name = get_metadata(eid) + ".txt"
                with open(destination / name, "w", encoding="utf-8") as f:
                    f.write(r.text)
                return name
        except:
            continue
    return None

def fetch_top_100(text_dir):
    url = "https://www.gutenberg.org/browse/scores/top"
    html = requests.get(url).text
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select("ol:nth-of-type(1) li a[href*='/ebooks/']")[:100]
    ids = [link["href"].split("/")[-1] for link in links]
    text_dir.mkdir(parents=True, exist_ok=True)
    downloaded = []
    for eid in tqdm(ids, desc="Downloading texts"):
        fname = try_download(eid, text_dir)
        if fname:
            downloaded.append(fname)
    return downloaded

def scan_file_for_haikus(path):
    with open(path, encoding="utf-8", errors="ignore") as f:
        raw = f.read()
    clean = clean_gutenberg_text(raw)
    return detect_haikus(clean, patterns=[[5, 7, 5], [3, 5, 3]])

def save_haikus_md(results, output_file):
    with open(output_file, "w", encoding="utf-8") as out:
        out.write("# Accidental Haikus\n\n")
        if not results:
            out.write("No haikus detected.\n")
        for title, haikus in results.items():
            for h in haikus:
                out.write("---\n\n")
                out.write(f"### From *{title}*\n\n")
                out.write("\n".join(line.strip() for line in h) + "\n\n")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--texts", default="/Users/tmbp/haiku_detector/texts", help="Text folder")
    parser.add_argument("--output", default="/Users/tmbp/haiku_detector/results/haiku_zine.md", help="Output Markdown file")
    args = parser.parse_args()

    text_dir = Path(args.texts)
    if not any(text_dir.glob("*.txt")):
        fetch_top_100(text_dir)

    files = list(text_dir.glob("*.txt"))
    results = {}
    for f in tqdm(files, desc="Scanning"):
        haikus = scan_file_for_haikus(f)
        if haikus:
            results[f.name] = haikus

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    save_haikus_md(results, args.output)
    print(f"✔ Done! Haikus saved to {args.output}")

if __name__ == "__main__":
    main()
