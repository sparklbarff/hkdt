#!/usr/bin/env python3
"""
Haiku Detector – Final Project

Downloads the top 100 most popular texts from Project Gutenberg,
detects 5-7-5 or 3-5-3 haikus using NLTK, and outputs results
in Markdown format to /Users/tmbp/haiku_detector/results/haiku_zine.md
"""

import re
import argparse
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import cmudict
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import nltk

nltk.download('punkt')
nltk.download('cmudict')

cmu_dict = cmudict.dict()

def count_syllables(word):
    word = word.lower()
    if word in cmu_dict:
        return min(len([ph for ph in pron if ph[-1].isdigit()]) for pron in cmu_dict[word])
    return len(re.findall(r"[aeiouy]+", word))

def line_syllable_count(line):
    words = word_tokenize(line)
    return sum(count_syllables(word) for word in words if word.isalpha())

def is_haiku(trio, pattern):
    return all(line_syllable_count(line) == count for line, count in zip(trio, pattern))

def clean_gutenberg_text(text):
    start = re.search(r"\*\*\* START OF .*? \*\*\*", text)
    end = re.search(r"\*\*\* END OF .*? \*\*\*", text)
    if start and end:
        return text[start.end():end.start()].strip()
    return text

def try_download(eid, destination):
    urls = [
        f"https://www.gutenberg.org/files/{eid}/{eid}-0.txt",
        f"https://www.gutenberg.org/files/{eid}/{eid}.txt"
    ]
    for url in urls:
        try:
            r = requests.get(url, timeout=10)
            if r.ok and "Title:" in r.text:
                with open(destination / f"{eid}.txt", "w", encoding="utf-8") as f:
                    f.write(r.text)
                return True
        except:
            pass
    return False

def fetch_top_100(text_dir):
    url = "https://www.gutenberg.org/browse/scores/top"
    html = requests.get(url).text
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select("ol:nth-of-type(1) li a[href*='/ebooks/']")[:100]
    ids = [link["href"].split("/")[-1] for link in links]
    text_dir.mkdir(parents=True, exist_ok=True)
    for eid in tqdm(ids, desc="Downloading texts"):
        try_download(eid, text_dir)

def scan_file_for_haikus(path, form):
    pattern = [int(n) for n in form.split("-")]
    with open(path, encoding="utf-8", errors="ignore") as f:
        text = clean_gutenberg_text(f.read())
    sents = sent_tokenize(text)
    return [sents[i:i+3] for i in range(len(sents)-2) if is_haiku(sents[i:i+3], pattern)]

def save_haikus_md(results, output_file):
    with open(output_file, "w", encoding="utf-8") as out:
        out.write("# Haiku Harvest\n\n")
        if not results:
            out.write("No haikus detected.\n")
        for book, haikus in results.items():
            for h in haikus:
                out.write("---\n\n")
                out.write(f"### From *{book}*\n\n")
                out.write("\n".join(line.strip() for line in h) + "\n\n")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--texts", default="/Users/tmbp/haiku_detector/texts", help="Text storage path")
    parser.add_argument("--form", default="5-7-5", help="Haiku pattern")
    parser.add_argument("--output", default="/Users/tmbp/haiku_detector/results/haiku_zine.md", help="Markdown output path")
    args = parser.parse_args()

    text_dir = Path(args.texts)
    if not any(text_dir.glob("*.txt")):
        fetch_top_100(text_dir)

    results = {}
    files = list(text_dir.glob("*.txt"))

    with ThreadPoolExecutor() as pool:
        futures = {pool.submit(scan_file_for_haikus, f, args.form): f for f in files}
        for fut in tqdm(as_completed(futures), total=len(futures), desc="Scanning"):
            f = futures[fut]
            haikus = fut.result()
            if haikus:
                results[f.name] = haikus

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    save_haikus_md(results, args.output)
    print(f"✔ Done! Haikus saved to {args.output}")

if __name__ == "__main__":
    main()
