import os
import json
import re
import csv
from tqdm import tqdm
from utils.hebrew_tokenizer import get_nikud_mask, NIKUD_PATTERN

# # Nikud (vowel marks) Unicode range
# NIKUD_PATTERN = re.compile(
#     '['
#     '\u05B0'  # sheva
#     '\u05B1'  # hataf segol
#     '\u05B2'  # hataf patah
#     '\u05B3'  # hataf qamats
#     '\u05B4'  # hiriq
#     '\u05B5'  # tsere
#     '\u05B6'  # segol
#     '\u05B7'  # patah
#     '\u05B8'  # qamats
#     '\u05B9'  # holam
#     '\u05BB'  # qubuts
#     '\u05BC'  # dagesh or mapiq
#     '\u05BD'  # meteg
#     '\u05BF'  # rafe (rare)
#     '\u05C1'  # shin dot
#     '\u05C2'  # sin dot
#     '\u05C7'  # qamats qatan
#     ']'
# )

def has_nikud(word: str) -> bool:
    """Check if a word contains nikud (vowel marks)."""
    return bool(NIKUD_PATTERN.search(word))

def split_sentences(text: str):
    """Naive sentence splitter for Hebrew."""
    return re.split(r'[.!?]\s+', text)

# def nikud_mask(text, tokenizer):
#     """
#     Returns a mask (list of 0/1) for each token in the sentence,
#     where 1 means the token contains at least one nikud mark.
#     """
#     tokens = tokenizer.tokenize(text)
#     mask = [1 if NIKUD_PATTERN.search(tok) else 0 for tok in tokens]
#     return tokens, mask

def extract_dataset(folder, output_file="dataset.csv", save_every=1000):
    """
    Walk through WikiExtractor JSON files and extract sentences
    that have BOTH nikud and non-nikud words.
    Save to CSV: text, nikud_mask
    Saves incrementally every `save_every` rows.
    """
    all_files = []
    for root, _, filenames in os.walk(folder):
        for filename in filenames:
            all_files.append(os.path.join(root, filename))

    print(f"📂 Found {len(all_files)} JSON files to process")

    # Open output file in write mode first → write header
    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "nikud_mask", "article_title", "article_length"])
        writer.writeheader()
        
    buffer = []
    total_saved = 0
        
    for path in tqdm(all_files, desc="Processing files"):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                # try:
                article = json.loads(line)
                text = article.get("text", "")
                title = article.get("title", "")
                # except json.JSONDecodeError:
                #     continue

                # Split into sentences
                sentences = split_sentences(text)
                for sent in sentences:
                    # words = sent.split()
                    # if not words:
                    #     continue
                    if not has_nikud(sent):
                        continue  # Skip sentences without any nikud

                    _, nikud_mask = get_nikud_mask(sent)
                    # print(sent, nikud_mask)

                    # Strict filtering: must contain at least one of each
                    if 1 in nikud_mask and 0 in nikud_mask:
                        buffer.append({
                            "text": sent.strip(),
                            "nikud_mask": nikud_mask,
                            "article_title": title,
                            "article_length": len(text.split())
                        })
                        
                        if len(buffer) >= save_every:
                            with open(output_file, "a", encoding="utf-8", newline="") as f:
                                writer = csv.DictWriter(f, fieldnames=["text", "nikud_mask", "article_title", "article_length"])
                                writer.writerows(buffer)
                            total_saved += len(buffer)
                            buffer = []
                            print(f"💾 Saved {total_saved} rows so far...")

    # Save leftovers
    if buffer:
        with open(output_file, "a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["text", "nikud_mask", "article_title", "article_length"])
            writer.writerows(buffer)
        total_saved += len(buffer)

    print(f"✅ Finished! Dataset saved to {output_file}, total {total_saved} rows")


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    current_directory = os.getcwd()
    print(f"Current directory: {current_directory}")
    folder = "output"  # output of WikiExtractor
    print(f"Extracting dataset from folder: {folder}")
    extract_dataset(folder, output_file="hebrew_nikud_dataset.csv")
