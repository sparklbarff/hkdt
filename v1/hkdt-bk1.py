#!/usr/bin/env python3
import os
import re
import argparse
from pathlib import Path
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import cmudict
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import nltk

nltk.download('punkt')
nltk.download('cmudict')

cmu_dict = cmudict.dict()

# Syllable count using CMUdict or fallback
def count_syllables(word):
    word = word.lower()
    if word in cmu_dict:
        return min(len([ph for ph in pron if ph[-1].isdigit()]) for pron in cmu_dict[word])
    return len(re.findall(r"[aeiouy]+", word))

# Total syllables in a line
def line_syllable_count(line):
    words = word_tokenize(line)
    return sum(count_syllables(word) for word in words if word.isalpha())

# Check if 3 lines match haiku pattern
def is_haiku(trio, pattern):
    return all(line_syllable_count(line) == syllables for line, syllables in zip(trio, pattern))

# Remove Gutenberg boilerplate
def clean_gutenberg_text(text):
    start = re.search(r"\*\*\* START OF .*? \*\*\*", text)
    end = re.search(r"\*\*\* END OF .*? \*\*\*", text)
    if start and end:
        return text[start.end():end.start()].strip()
    return text

# Scan one file for haikus
def scan_file_for_haikus(path, form):
    pattern = [int(x) for x in form.split("-")]
    with open(path, encoding='utf-8') as f:
        text = clean_gutenberg_text(f.read())
    sents = sent_tokenize(text)
    return [sents[i:i+3] for i in range(len(sents)-2) if is_haiku(sents[i:i+3], pattern)]

# Save haikus to markdown
def save_haikus_md(results, out_path):
    with open(out_path, "w", encoding='utf-8') as f:
        f.write("# Haiku Harvest\n\n")
        for src, haikus in results.items():
            for h in haikus:
                f.write("---\n\n")
                f.write(f"### From *{src}*\n\n")
                f.write("\n".join(line.strip() for line in h) + "\n\n")

# CLI entry
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--texts", default="texts", help="Folder with .txt files")
    p.add_argument("--form", default="5-7-5", help="Haiku form like 5-7-5 or 3-5-3")
    p.add_argument("--output", default="results/haiku_zine.md", help="Markdown output path")
    args = p.parse_args()

    text_dir = Path(args.texts)
    results = {}
    files = list(text_dir.rglob("*.txt"))

    with ThreadPoolExecutor() as ex:
        futures = {ex.submit(scan_file_for_haikus, f, args.form): f for f in files}
        for fut in tqdm(as_completed(futures), total=len(futures), desc="Scanning"):
            f = futures[fut]
            haikus = fut.result()
            if haikus:
                results[f.name] = haikus

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    save_haikus_md(results, args.output)
    print(f"✔ Haikus saved to {args.output}")

if __name__ == "__main__":
    main()
