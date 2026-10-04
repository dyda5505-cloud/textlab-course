"""Deterministic Unicode text analysis, shared by the worker and tests."""
import re
from collections import Counter

WORD_PATTERN = re.compile(r"[^\W_]+(?:['’][^\W_]+)*", re.UNICODE)

def tokenize(text):
    return WORD_PATTERN.findall(text.casefold())

def analyze(text):
    words = tokenize(text)
    counts = Counter(words)
    frequent = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:10]
    return {
        'characters': len(text),
        'words': len(words),
        'unique_words': len(counts),
        'top_words': [{'word': word, 'count': count} for word, count in frequent],
    }
