#!/usr/bin/env python3
"""
Haiku Detector - hkdt.py

Scans all .txt files in a `texts/` folder for haikus (5-7-5 or 3-5-3),
and outputs results in Markdown format to `results/haiku_zine.md`.
"""

import os
import re
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from pathlib import Path
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import cmudict
import nltk

# Ensure required NLTK corpora are availablenltk.download('punkt')
# Ensure required NLTK corpora are availablenltk.download('cmudict')

# Load CMU Pronouncing Dictionarycmu_dict = cmudict.dict()


# Count syllables in a word using CMUdict or fallback heuristicdef count_syllables(word):
    word = word.lower()
    if word in cmu_dict:
        return min(len([ph for ph in pron if ph[-1].isdigit()]) for pron in cmu_dict[word])
    else:
        # fallback: basic heuristic
        return len(re.findall(r"[aeiouy]+", word.lower()))


# Count total syllables in a linedef line_syllable_count(line):
    words = word_tokenize(line)
    return sum(count_syllables(word) for word in words if word.isalpha())


# Check if a trio of lines matches a syllable pattern like 5-7-5 or 3-5-3def is_haiku(trio, pattern):
    return all(line_syllable_count(line) == syllables for line, syllables in zip(trio, pattern))


# Strip Project Gutenberg header/footer text using regex markersdef clean_gutenberg_text(text):
    start_re = re.compile(r"\*\*\* START OF (.*?) \*\*\*")
    end_re = re.compile(r"\*\*\* END OF (.*?) \*\*\*")
    start = start_re.search(text)
    end = end_re.search(text)
    if start and end:
        return text[start.end():end.start()].strip()
    return text


# Scan one file for haiku triplets and return matchesdef scan_file_for_haikus(path, form):
    pattern = [int(x) for x in form.split("-")]
    with open(path, encoding='utf-8') as f:
        raw = f.read()
    clean_text = clean_gutenberg_text(raw)
    sentences = sent_tokenize(clean_text)
    haikus = []
    for i in range(len(sentences) - 2):
        trio = sentences[i:i+3]
        if is_haiku(trio, pattern):
            haikus.append(trio)
    return haikus


# Save all found haikus to a Markdown zine filedef save_haikus_md(haikus_by_file, output_path):
    with open(output_path, "w", encoding='utf-8') as out:
        out.write("# Haiku Harvest: From the Gutenberg Top 100\n\n")
        for filename, haikus in haikus_by_file.items():
            for h in haikus:
                out.write("---\n\n")
                out.write(f"### Found in *{filename}*\n\n")
                for line in h:
                    out.write(line.strip() + "\n")
                out.write("\n")


# Parse CLI args and execute haiku detection pipelinedef main():
    parser = argparse.ArgumentParser(description="Scan .txt files for haikus.")
    parser.add_argument("--texts", default="texts", help="Folder with .txt files")
    parser.add_argument("--form", default="5-7-5", help="Haiku form, e.g., 5-7-5 or 3-5-3")
    parser.add_argument("--output", default="results/haiku_zine.md", help="Markdown file output path")
    args = parser.parse_args()

    text_dir = Path(args.texts)
    results = {}

    files = list(text_dir.rglob("*.txt"))
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(scan_file_for_haikus, file, args.form): file for file in files}
        for future in tqdm(as_completed(futures), total=len(futures), desc='Scanning'):
            file = futures[future]
            haikus = future.result()
            if haikus:
                results[file.name] = haikus
        haikus = scan_file_for_haikus(file, args.form)
        if haikus:
            results[file.name] = haikus

    output_dir = Path(args.output).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    save_haikus_md(results, args.output)
    print(f"✔ Haikus saved to {args.output}")

if __name__ == "__main__":
    main()
