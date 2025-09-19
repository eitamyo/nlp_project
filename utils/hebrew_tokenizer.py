# hebrew_tokenizer.py
import re
from transformers import AutoTokenizer

# Load tokenizer once
TOKENIZER_NAME = "dicta-il/dictabert-large-char-menaked"
tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_NAME)

# Regex for Hebrew nikud marks
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

def get_nikud_mask(text: str):
    """
    Returns a mask aligned with tokenizer input_ids,
    where 1 means the corresponding token span in the *original text*
    contained at least one nikud mark.
    """
    # Step 1: Tokenize with offsets
    enc = tokenizer(text, return_offsets_mapping=True)
    offsets = enc["offset_mapping"]

    # Step 2: For each token, check substring of original text
    mask = []
    for (start, end) in offsets:
        if start == end:  # special tokens
            mask.append(0)
            continue
        substring = text[start:end+1]
        mask.append(1 if NIKUD_PATTERN.search(substring) else 0)

    return enc["input_ids"], mask
