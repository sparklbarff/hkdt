import requests, re, nltk
from bs4 import BeautifulSoup
from nltk.corpus import cmudict
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk import pos_tag
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

nltk.download('cmudict')
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

d = cmudict.dict()
analyzer = SentimentIntensityAnalyzer()

def clean_gutenberg_text(text):
    start_pattern = r"\*\*\* START OF (THE|THIS) PROJECT GUTENBERG EBOOK .* \*\*\*"
    end_pattern = r"\*\*\* END OF (THE|THIS) PROJECT GUTENBERG EBOOK .* \*\*\*"
    start_match = re.search(start_pattern, text, re.IGNORECASE)
    end_match = re.search(end_pattern, text, re.IGNORECASE)
    return text[start_match.end():end_match.start()].strip() if start_match and end_match else text.strip()

def count_syllables(word):
    word = word.lower()
    if word in d:
        return min(len([y for y in pronunciation if y[-1].isdigit()]) for pronunciation in d[word])
    return max(1, len(re.findall(r'[aeiouy]+', word)))

def is_sentence_like(line):
    tagged = pos_tag(word_tokenize(line))
    has_verb = any(tag.startswith('VB') for _, tag in tagged)
    has_noun = any(tag.startswith('NN') or tag.startswith('PRP') for _, tag in tagged)
    return has_verb and has_noun

def is_junky(line):
    return (
        line.isupper() or
        re.match(r'^[0-9\s\W]+$', line) or
        len(set(word_tokenize(line.lower()))) < 3
    )

def detect_haikus(text):
    sentences = sent_tokenize(text)
    results = []

    for sentence in sentences:
        phrases = [phrase.strip() for phrase in re.split(r'[,:;\.\?!\n]', sentence) if phrase.strip()]
        for i in range(len(phrases)-2):
            lines = phrases[i:i+3]
            syll_counts = [sum(count_syllables(w) for w in word_tokenize(line) if w.isalpha()) for line in lines]

            if (
                syll_counts == [5, 7, 5]
                and all(is_sentence_like(line) for line in lines)
                and all(not is_junky(line) for line in lines)
            ):
                haiku_text = " ".join(lines)
                sentiment = analyzer.polarity_scores(haiku_text)['compound']
                results.append((sentiment, lines))

    return results

def search_gutenberg(query, max_results=5):
    url = f"https://www.gutenberg.org/ebooks/search/?query={requests.utils.quote(query)}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    results = []
    for link in soup.select('li.booklink')[:max_results]:
        title_tag = link.select_one('.title')
        author_tag = link.select_one('.subtitle')
        href = link.find('a')['href']
        book_id = href.split('/')[-1]
        title = title_tag.text.strip()
        author = author_tag.text.strip() if author_tag else "Unknown"
        results.append((book_id, title, author))
    return results

def download_book_text(book_id):
    urls = [
        f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt",
        f"https://www.gutenberg.org/files/{book_id}/{book_id}.txt",
        f"https://www.gutenberg.org/files/{book_id}/{book_id}-8.txt"
    ]
    for url in urls:
        response = requests.get(url)
        if response.status_code == 200:
            return clean_gutenberg_text(response.text)
    raise ValueError("Could not download book text.")

def main():
    while True:
        query = input("\n🔍 Enter a book title, author, or keyword: ").strip()
        matches = search_gutenberg(query)

        if not matches:
            print("❌ No results found. Try another search.")
            continue

        print("\n📚 Matches found:")
        for i, (book_id, title, author) in enumerate(matches, 1):
            print(f"{i}. {title} by {author} (ID: {book_id})")

        sel = input("\nSelect a book by number (or 'q' to quit): ").strip()
        if sel.lower() == 'q':
            break
        if not sel.isdigit() or not (1 <= int(sel) <= len(matches)):
            print("❌ Invalid selection.")
            continue

        book_id, title, author = matches[int(sel)-1]
        print(f"\n📖 Downloading: {title} by {author}...\n")
        try:
            text = download_book_text(book_id)
        except Exception as e:
            print(f"❌ Failed to download: {e}")
            continue

        mood = input("Do you want [happy] or [sad] haikus? ").strip().lower()
        if mood not in {"happy", "sad"}:
            print("❌ Invalid mood. Please type 'happy' or 'sad'.")
            continue

        print("\n🔍 Detecting haikus...\n")
        haikus = detect_haikus(text)
        if not haikus:
            print("😞 No valid haikus found in this text.")
        else:
            sorted_haikus = sorted(haikus, key=lambda x: x[0], reverse=(mood == "happy"))
            print(f"\n🎴 {mood.capitalize()} Haikus from '{title}':\n")
            for idx, (score, lines) in enumerate(sorted_haikus[:10], 1):
                print(f"Haiku #{idx} (sentiment: {score:+.2f}):")
                for line in lines:
                    print(f"  {line}")
                print()

        again = input("\n🔁 Search another book? (y/n): ").strip().lower()
        if again != 'y':
            break

if __name__ == '__main__':
    main()
