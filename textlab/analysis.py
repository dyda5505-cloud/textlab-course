import re

def analyze(text):
    words = re.findall(r"[^\W_]+(?:['’][^\W_]+)*", text.casefold(), re.UNICODE)
    counts = {}
    for word in words:
        if word in counts:
            counts[word] += 1
        else:
            counts[word] = 1
    items = list(counts.items())
    items.sort(key=lambda item: (-item[1], item[0]))
    result = []
    for word, count in items[:10]:
        result.append({'word': word, 'count': count})
    return {'characters': len(text), 'words': len(words),
            'unique_words': len(counts), 'top_words': result}
