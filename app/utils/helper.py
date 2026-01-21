import re
from pathlib import Path
from typing import List, Optional, Set

from app.logger import logger

_ASCII_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


def load_stopwords(path: Optional[str]) -> Set[str]:
    if not path:
        return set()

    p = Path(path)
    if not p.exists():
        logger.warning(f"[RetrievalService] stopwords file not found: {p}")
        return set()

    out: Set[str] = set()
    for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        w = line.strip()
        if not w or w.startswith("#"):
            continue
        out.add(w)
    return out


def _is_zh_char(ch: str) -> bool:
    return "\u4e00" <= ch <= "\u9fff"


def ngram_tokenize_unigram_bigram(text: str, *, stopwords: Set[str]) -> List[str]:
    if not text:
        return []

    s = text.strip()
    if not s:
        return []

    tokens: List[str] = []

    for m in _ASCII_TOKEN_RE.finditer(s):
        w = m.group(0).lower()
        if w and w not in stopwords:
            tokens.append(w)

    buf: List[str] = []

    def flush_buf() -> None:
        nonlocal buf
        if not buf:
            return

        for ch in buf:
            if ch and ch not in stopwords:
                tokens.append(ch)

        for i in range(len(buf) - 1):
            bg = buf[i] + buf[i + 1]
            if bg and bg not in stopwords:
                tokens.append(bg)

        buf = []

    for ch in s:
        if _is_zh_char(ch):
            buf.append(ch)
        else:
            flush_buf()
    flush_buf()

    return tokens
