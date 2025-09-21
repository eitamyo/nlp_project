# hebrew_tokenizer.py
import re
from transformers import AutoModel, AutoTokenizer
from math import log2
import torch

# Load tokenizer once
MODEL_NAME = "dicta-il/dictabert-large-char-menaked"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME, trust_remote_code=True)

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

# Regex for Hebrew letters
HEBREW_LETTER_PATTERN = re.compile(r'[\u05D0-\u05EA]')


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


def calculate_entropy(dist):
    """
    Calculate the entropy of a probability distribution tensor.
    """
    return -sum(p.item() * log2(p.item()) for p in dist if p.item() > 0)

def is_ambiguous_char(dist, entropy_threshold=1.0, margin_threshold=0.2, maxprob_threshold=0.7):
    """
    Determine if a character is ambiguous based on its predicted distribution.
    """
    sorted_probs, _ = torch.sort(dist, descending=True)
    p1, p2 = sorted_probs[0].item(), sorted_probs[1].item()

    entropy = calculate_entropy(dist)
    margin = p1 - p2
    max_prob = p1

    return (entropy > entropy_threshold) or (margin < margin_threshold) or (max_prob < maxprob_threshold)

def get_nikud_uncertainty(text,
                          top_k=5,
                          entropy_threshold=1.0,
                          margin_threshold=0.2,
                          maxprob_threshold=0.7):
    """
    Identify ambiguous characters in the text according to nikud predictions.
    Returns a mask aligned with tokenizer input_ids,
    where 1 means the corresponding character in the *original text*
    is considered ambiguous.
    Also returns a list of ambiguous characters with details.
    """
    # Tokenize
    inputs = tokenizer(text, return_tensors="pt",
                       return_offsets_mapping=True, truncation=True)
    
    offsets = inputs.pop("offset_mapping")[0]

    with torch.no_grad():
        outputs = model(**inputs)   # MenakedOutput
        # shape [seq_len, num_nikud_classes]
        nikud_probs = torch.softmax(outputs.logits.nikud_logits[0], dim=-1)
        shin_probs = torch.softmax(outputs.logits.shin_logits[0], dim=-1)

    # id2label = model.config.nikud_classes  # list of all nikud symbols

    ambiguous = []
    mask = []
    for i, (start, end) in enumerate(offsets):
        if end - start != 1:  # skip special tokens / padding
            mask.append(0)
            continue
        char = text[start:end]
        if not HEBREW_LETTER_PATTERN.match(char):  # not a Hebrew letter
            mask.append(0)
            continue
        
        dist = nikud_probs[i]
        is_ambig = is_ambiguous_char(dist, entropy_threshold, margin_threshold, maxprob_threshold)
        
        if char == "ש":
            s_probs = shin_probs[i]
            is_ambig_shin = is_ambiguous_char(s_probs, entropy_threshold, margin_threshold, maxprob_threshold)
            is_ambig = is_ambig or is_ambig_shin

        if is_ambig:
            mask.append(1)
            ambiguous.append({
                "char": char,
                "position": (start, end),
                # "entropy": entropy,
                # "margin": margin,
                # "max_prob": max_prob,
                # "top_candidates": [
                #     (id2label[sorted_ids[j].item()], sorted_probs[j].item())
                #     for j in range(min(top_k, len(sorted_ids)))
                # ]
            })
        else:
            mask.append(0)
    return mask, ambiguous

def convert_token_to_word_mask(text: str, mask):
    """
    Convert a token-level mask to a word-level mask.
    A word is considered to have nikud if any of its tokens have nikud.
    """
    tokens = tokenizer.tokenize(text)
    word_mask = []
    current_word_has_nikud = False

    for token, m in zip(tokens, mask):
        if HEBREW_LETTER_PATTERN.match(token):  # part of a word
            if m == 1:
                current_word_has_nikud = True
        else:  # new word
            if current_word_has_nikud:
                word_mask.append(1)
            elif len(word_mask) > 0:  # not the first word
                word_mask.append(0)
            current_word_has_nikud = (m == 1)

    # Append mask for the last word
    if current_word_has_nikud:
        word_mask.append(1)
    elif len(word_mask) > 0:
        word_mask.append(0)

    return word_mask