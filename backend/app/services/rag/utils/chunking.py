import re
from typing import List
from app.services.rag.config.settings import settings

def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
    strategy = (settings.CHUNK_STRATEGY or "semantic").lower()
    size = chunk_size or settings.CHUNK_SIZE or 1200
    ov = overlap or settings.CHUNK_OVERLAP or 120
    
    if strategy == "fixed":
        chunks = []
        start = 0
        L = len(text)
        while start < L:
            end = min(start + size, L)
            chunks.append(text[start:end])
            start = end - ov
            if start >= end:
                start = end
        return chunks
        
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paras:
        paras = [text]

    def split_sentences(t: str) -> List[str]:
        t = t.replace("\r", "\n")
        sents = re.split(r"(?<=[。！？!?；;．.])\s+", t)
        sents = [s.strip() for s in sents if s.strip()]
        return sents

    token_count = None
    if settings.CHUNK_TOKENIZER:
        try:
            import tiktoken
            enc = tiktoken.get_encoding(settings.CHUNK_TOKENIZER)
            token_count = lambda s: len(enc.encode(s))
        except Exception:
            token_count = None

    def measure(s: str) -> int:
        if token_count:
            return token_count(s)
        return len(s)

    chunks = []
    cur = []
    cur_len = 0
    sentences = []
    for p in paras:
        sentences.extend(split_sentences(p))
    for sent in sentences:
        m = measure(sent)
        if cur_len + m <= size or not cur:
            cur.append(sent)
            cur_len += m
        else:
            chunks.append("".join(cur))
            overlap_sents = []
            if ov > 0:
                rev = []
                acc = 0
                for s in reversed(cur):
                    ms = measure(s)
                    if acc + ms <= ov:
                        rev.append(s)
                        acc += ms
                    else:
                        break
                overlap_sents = list(reversed(rev))
            cur = overlap_sents + [sent]
            cur_len = sum(measure(s) for s in cur)
    if cur:
        chunks.append("".join(cur))
    return chunks
