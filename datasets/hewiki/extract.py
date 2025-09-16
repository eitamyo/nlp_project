import os
import json
import re
import csv

# Regex ranges
HEBREW_LETTER = r'[\u05D0-\u05EA]'
NIKUD = r'[\u0591-\u05C7]'

word_re = re.compile(rf'{HEBREW_LETTER}+{NIKUD}?{HEBREW_LETTER}*')
nikud_re = re.compile(NIKUD)

def has_nikud(word: str) -> bool:
    """Check if a word contains nikud (vowel marks)."""
    return bool(nikud_re.search(word))

def split_sentences(text: str):
    """Naive sentence splitter for Hebrew."""
    return re.split(r'[.!?]\s+', text)

def extract_dataset(folder, output_file="dataset.csv", max_files=100):
    """
    Walk through WikiExtractor JSON files and extract sentences/paragraphs
    that have both nikud and non-nikud words.
    Save to CSV: id, text, words, nikud_mask
    """
    dataset = []
    files = 0

    for root, _, filenames in os.walk(folder):
        for filename in filenames:
            # if not filename.endswith(".json"):
            #     continue
            path = os.path.join(root, filename)
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    # try:
                    article = json.loads(line)
                    text = article.get("text", "")
                    # except json.JSONDecodeError:
                    #     continue

                    # Split into sentences
                    sentences = split_sentences(text)
                    for sent in sentences:
                        words = sent.split()
                        if not words:
                            continue

                        # Compute which words have nikud
                        nikud_mask = [int(has_nikud(w)) for w in words]

                        # Keep only if there is a mix (some with, some without)
                        if 1 in nikud_mask and 0 in nikud_mask:
                            dataset.append({
                                "text": sent.strip(),
                                "words": words,
                                "nikud_mask": nikud_mask
                            })

            files += 1
            if files >= max_files:
                break
        if files >= max_files:
            break

    # Save as CSV
    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "words", "nikud_mask"])
        writer.writeheader()
        for row in dataset:
            writer.writerow({
                "text": row["text"],
                "words": " ".join(row["words"]),
                "nikud_mask": " ".join(map(str, row["nikud_mask"]))
            })

    print(f"✅ Dataset saved to {output_file}, {len(dataset)} examples")

if __name__ == "__main__":
    folder = "output"  # output of WikiExtractor
    extract_dataset(folder, output_file="hebrew_nikud_dataset.csv", max_files=1000)
