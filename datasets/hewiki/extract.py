import os
import json
import re
import csv

# Nikud (vowel marks) Unicode range
NIKUD_PATTERN = re.compile(
    '['
    '\u05B0'  # sheva
    '\u05B1'  # hataf segol
    '\u05B2'  # hataf patah
    '\u05B3'  # hataf qamats
    '\u05B4'  # hiriq
    '\u05B5'  # tsere
    '\u05B6'  # segol
    '\u05B7'  # patah
    '\u05B8'  # qamats
    '\u05B9'  # holam
    '\u05BB'  # qubuts
    '\u05BC'  # dagesh or mapiq
    '\u05BD'  # meteg
    '\u05BF'  # rafe (rare)
    '\u05C1'  # shin dot
    '\u05C2'  # sin dot
    '\u05C7'  # qamats qatan
    ']'
)

def has_nikud(word: str) -> bool:
    """Check if a word contains nikud (vowel marks)."""
    return bool(NIKUD_PATTERN.search(word))

def split_sentences(text: str):
    """Naive sentence splitter for Hebrew."""
    return re.split(r'[.!?]\s+', text)

def extract_dataset(folder, output_file="dataset.csv", max_files=100):
    """
    Walk through WikiExtractor JSON files and extract sentences
    that have BOTH nikud and non-nikud words.
    Save to CSV: text, words, nikud_mask
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

                        nikud_mask = [int(has_nikud(w)) for w in words]

                        # Strict filtering: must contain at least one of each
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
