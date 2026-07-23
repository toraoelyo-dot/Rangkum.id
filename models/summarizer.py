from transformers import pipeline


summarizer = pipeline(
    "summarization",
    model="sshleifer/distilbart-cnn-12-6"
)

# Batas token maksimum model (dalam karakter ~3500 aman)
MAX_CHUNK_CHARS = 3000


def chunk_text(text, max_chars=MAX_CHUNK_CHARS):
    """
    Memecah teks panjang menjadi beberapa bagian (chunks)
    berdasarkan kalimat agar tidak memotong di tengah kalimat.
    """
    sentences = text.replace('\n', ' ').split('. ')
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        # Tambahkan titik yang dihilangkan saat split
        sentence = sentence.strip()
        if not sentence:
            continue

        candidate = current_chunk + sentence + ". "

        if len(candidate) <= max_chars:
            current_chunk = candidate
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            # Jika satu kalimat lebih panjang dari max_chars, potong langsung
            if len(sentence) > max_chars:
                for i in range(0, len(sentence), max_chars):
                    chunks.append(sentence[i:i + max_chars])
                current_chunk = ""
            else:
                current_chunk = sentence + ". "

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def summarize_document(text):
    """
    Meringkas dokumen dengan cara memecah teks panjang menjadi
    beberapa bagian lalu menggabungkan hasilnya.
    """
    # Bersihkan teks dari spasi berlebih
    text = " ".join(text.split())

    # Jika teks pendek, langsung diringkas
    if len(text) <= MAX_CHUNK_CHARS:
        chunks = [text]
    else:
        chunks = chunk_text(text)

    summaries = []

    for chunk in chunks:
        # Pastikan chunk cukup panjang untuk diringkas (minimal 100 karakter)
        if len(chunk.strip()) < 100:
            summaries.append(chunk.strip())
            continue

        try:
            result = summarizer(
                chunk,
                max_length=150,
                min_length=30,
                do_sample=False,
                truncation=True
            )
            summaries.append(result[0]["summary_text"].strip())
        except Exception:
            # Jika gagal, tambahkan chunk asli sebagai fallback
            words = chunk.split()
            summaries.append(" ".join(words[:80]))

    # Gabungkan semua ringkasan
    combined = " ".join(summaries)

    # Batasi panjang ringkasan akhir maksimum 500 kata
    words = combined.split()
    if len(words) > 500:
        combined = " ".join(words[:500])

    return combined
