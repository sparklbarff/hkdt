import requests, re, nltk
from bs4 import BeautifulSoup
from nltk.corpus import cmudict
from nltk.tokenize import word_tokenize, sent_tokenize
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from nltk import pos_tag

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

def fetch_top_books():
    response = requests.get("https://www.gutenberg.org/browse/scores/top1000.php")
    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.select('ol li a[href^="/ebooks/"]')[:100]
    books = []
    for link in links:
        book_id = link['href'].split('/')[-1]
        title = link.get_text()
        books.append((book_id, title))
    return books

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
    books = fetch_top_books()

    print("\n📚 Available Texts:\n")
    for i, (_, title) in enumerate(books):
        print(f"{i+1}. {title}")

    choice = input("\nEnter a number (1–100) or exact title: ").strip()

    if choice.isdigit():
        index = int(choice) - 1
        if index < 0 or index >= len(books):
            print("Invalid number.")
            return
    else:
        matches = [i for i, (_, title) in enumerate(books) if title.lower() == choice.lower()]
        if not matches:
            print("Book not found.")
            return
        index = matches[0]

    book_id, title = books[index]
    print(f"\n📖 Downloading: {title}...")
    text = download_book_text(book_id)

    mood = input("\nDo you want [happy] or [sad] haikus? ").strip().lower()
    if mood not in {"happy", "sad"}:
        print("Invalid mood.")
        return

    print("\n🔍 Detecting haikus...\n")
    haikus = detect_haikus(text)

    if not haikus:
        print("No haikus found.")
        return

    sorted_haikus = sorted(haikus, key=lambda x: x[0], reverse=(mood == "happy"))

    print(f"🎴 {mood.capitalize()} Haikus from '{title}':\n")
    for idx, (score, lines) in enumerate(sorted_haikus[:10], 1):  # Show top 10
        print(f"Haiku #{idx} (sentiment: {score:+.2f}):")
        for line in lines:
            print(f"  {line}")
        print()

if __name__ == '__main__':
    main()
