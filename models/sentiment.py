"""
Analisis Sentimen Hybrid
========================
Strategi:
1. VADER (vaderSentiment) — primary, rule-based, 3 label native, sangat andal
2. TextBlob              — secondary, sebagai validasi tambahan
3. Jika keduanya tersedia → gabungkan; jika tidak → pakai yang ada

VADER compound score:
  >= +0.05  → Positif
  <= -0.05  → Negatif
  antara    → Netral
"""

import re

# ── VADER ──────────────────────────────────────────────────
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _vader = SentimentIntensityAnalyzer()
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False

# ── TextBlob ────────────────────────────────────────────────
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False

# ── Metadata label ─────────────────────────────────────────
SENTIMENT_META = {
    "Positif": {"icon": "fa-face-smile",   "color": "#22c55e"},
    "Negatif": {"icon": "fa-face-frown",   "color": "#ef4444"},
    "Netral":  {"icon": "fa-face-meh",     "color": "#eab308"},
}


# ─────────────────────────────────────────────────────────────
# Helper: pecah teks menjadi chunk kalimat
# ─────────────────────────────────────────────────────────────
def _split_chunks(text: str, max_chars: int = 500) -> list:
    sentences = [s.strip() for s in re.split(r'[.!?]', text) if len(s.strip()) > 10]
    chunks, cur = [], ""
    for sent in sentences:
        if len(cur) + len(sent) < max_chars:
            cur += sent + ". "
        else:
            if cur.strip():
                chunks.append(cur.strip())
            cur = sent + ". "
    if cur.strip():
        chunks.append(cur.strip())
    return chunks or [text[:500]]


# ─────────────────────────────────────────────────────────────
# VADER analysis — mengembalikan compound score rata-rata
# ─────────────────────────────────────────────────────────────
def _score_vader(text: str) -> float | None:
    if not VADER_AVAILABLE:
        return None
    chunks = _split_chunks(text)
    total = 0.0
    for chunk in chunks:
        scores = _vader.polarity_scores(chunk)
        total += scores["compound"]
    return total / len(chunks)


# ─────────────────────────────────────────────────────────────
# TextBlob analysis — mengembalikan polarity rata-rata
# ─────────────────────────────────────────────────────────────
def _score_textblob(text: str) -> float | None:
    if not TEXTBLOB_AVAILABLE:
        return None
    try:
        chunks = _split_chunks(text)
        total = 0.0
        for chunk in chunks:
            total += TextBlob(chunk).sentiment.polarity
        return total / len(chunks)
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────
# FUNGSI UTAMA
# ─────────────────────────────────────────────────────────────
def analyze_sentiment(text: str) -> dict:
    """
    Menganalisis sentimen teks.
    Mengembalikan dict: label, score (0–1), icon, color.

    PENTING: kirim teks dengan kapitalisasi ASLI (bukan lowercase).
    """
    text = text.strip()

    if not text:
        return {
            "label": "Tidak Diketahui",
            "score": 0.0,
            "icon":  "fa-question",
            "color": "#94a3b8",
        }

    # ── Ambil skor dari masing-masing metode ──
    vader_compound  = _score_vader(text)
    textblob_polar  = _score_textblob(text)

    # ── Gabungkan skor ──
    if vader_compound is not None and textblob_polar is not None:
        # Bobot: VADER 60%, TextBlob 40%
        combined = vader_compound * 0.6 + textblob_polar * 0.4
    elif vader_compound is not None:
        combined = vader_compound
    elif textblob_polar is not None:
        combined = textblob_polar
    else:
        # Fallback: tidak ada library tersedia
        return {
            "label": "Netral",
            "score": 0.5,
            "icon":  SENTIMENT_META["Netral"]["icon"],
            "color": SENTIMENT_META["Netral"]["color"],
        }

    # ── Tentukan label ──
    if combined >= 0.05:
        label = "Positif"
        # Normalisasi confidence: 0.05–1.0 → 0.5–1.0
        score = 0.5 + min(combined, 1.0) * 0.5
    elif combined <= -0.05:
        label = "Negatif"
        score = 0.5 + min(abs(combined), 1.0) * 0.5
    else:
        label = "Netral"
        # Semakin mendekati 0, semakin yakin netral
        score = 0.5 + (0.05 - abs(combined)) * 2
        score = min(score, 0.85)

    meta = SENTIMENT_META[label]

    return {
        "label": label,
        "score": round(score, 4),
        "icon":  meta["icon"],
        "color": meta["color"],
    }
