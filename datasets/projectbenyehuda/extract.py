import os
import re
import csv
from tqdm import tqdm
from utils.hebrew_tokenizer import get_nikud_mask, NIKUD_PATTERN

def has_nikud(word: str) -> bool:
    """Check if a word contains nikud (vowel marks)."""
    return bool(NIKUD_PATTERN.search(word))

def split_sentences(text: str):
    """Naive sentence splitter for Hebrew. Strips newlines and multiple spaces."""
    # Replace newlines with spaces
    text = text.replace('\n', ' ')
    # Collapse multiple spaces into one
    text = re.sub(r'\s+', ' ', text)
    # Split into sentences
    return re.split(r'[.!?]\s+', text)

def extract_dataset(folder, output_file="dataset.csv", save_every=1000):
    """
    Walk through text files in the folder and extract sentences
    that have BOTH nikud and non-nikud words.
    Save to CSV: id, title, text, nikud_mask
    Skips the first two lines of each file.
    """
    all_files = [os.path.join(folder, fname) for fname in os.listdir(folder) if fname.endswith('.txt')]
    print(f"📂 Found {len(all_files)} text files to process")

    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "title", "text", "nikud_mask"])
        writer.writeheader()

    buffer = []
    total_saved = 0

    for path in tqdm(all_files, desc="Processing files"):
        filename = os.path.basename(path)
        if "_" not in filename:
            continue
        file_id, title_with_ext = filename.split("_", 1)
        title = title_with_ext.rsplit(".txt", 1)[0]

        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()[2:]  # skip first two lines
            text = "".join(lines)
            sentences = split_sentences(text)
            for sent in sentences:
                if not has_nikud(sent):
                    continue
                _, nikud_mask = get_nikud_mask(sent)
                nikud_mask_str = "".join(map(str, nikud_mask))

                if 1 in nikud_mask and 0 in nikud_mask and "00" in nikud_mask_str:
                    buffer.append({
                        "id": file_id,
                        "title": title,
                        "text": sent.strip(),
                        "nikud_mask": nikud_mask
                    })
                    if len(buffer) >= save_every:
                        with open(output_file, "a", encoding="utf-8", newline="") as f:
                            writer = csv.DictWriter(f, fieldnames=["id", "title", "text", "nikud_mask"])
                            writer.writerows(buffer)
                        total_saved += len(buffer)
                        buffer = []
                        print(f"💾 Saved {total_saved} rows so far...")

    if buffer:
        with open(output_file, "a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "title", "text", "nikud_mask"])
            writer.writerows(buffer)
        total_saved += len(buffer)

    print(f"✅ Finished! Dataset saved to {output_file}, total {total_saved} rows")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    folder = "output/benyehuda_modern_texts"  # folder with .txt files
    print(f"Extracting dataset from folder: {folder}")
    extract_dataset(folder, output_file="benyehuda_nikud_dataset.csv")