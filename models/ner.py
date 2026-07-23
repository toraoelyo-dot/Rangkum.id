"""
Pengenalan Entitas Bernama (NER) Hybrid Bahasa Indonesia (Edisi Akurat & Cerdas)
================================================================================
Menggabungkan kekuatan spaCy en_core_web_md dengan parser berbasis aturan (Rule-based Regex)
khusus Bahasa Indonesia.

Menggunakan penyaringan kapitalisasi yang ketat (capitalization check) pada entitas teks proper noun
(Orang, Organisasi, Lokasi, Tempat, Kegiatan, Peristiwa, Produk).

Ditambah dengan Logika Dekonstruksi Pintar (Smart Deconstruction):
Jika spaCy salah mengelompokkan kalimat panjang sebagai PERSON (misalnya: "Raka merasa beruntung..."),
sistem akan mengekstrak kata pertamanya saja ("Raka") sebagai subjek PERSON,
setelah memastikan kata tersebut bukan merupakan kata umum Bahasa Indonesia (seperti "Hasil", "Sebelum", "Pagi").

Mendukung 16 Kategori Entitas yang diminta oleh User:
  1. Orang, 2. Lokasi, 3. Tempat, 4. Organisasi, 5. Waktu, 6. Hari, 7. Tanggal, 
  8. Urutan, 9. Persentase, 10. Uang, 11. Jumlah, 12. Bilangan, 13. Peristiwa, 
  14. Cuaca, 15. Produk, 16. Kegiatan
"""

import re
import warnings
import spacy

warnings.filterwarnings("ignore", category=UserWarning, module="spacy")

# ── Lazy-load model ───────────────────────────────────────────
_nlp = None

def _load_model():
    global _nlp
    if _nlp is not None:
        return _nlp
    for model_name in ("en_core_web_md", "en_core_web_sm"):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                _nlp = spacy.load(model_name)
            return _nlp
        except OSError:
            continue
    return None


# ── Metadata Tampilan 16 Kategori Entitas ──────────────────────
LABEL_MAP = {
    # 1. Orang
    "PERSON":      {"label": "Orang",              "icon": "fa-user",           "color": "#6366f1"},
    # 2. Lokasi (Geopolitik seperti negara/kota/provinsi)
    "GPE":         {"label": "Lokasi",              "icon": "fa-flag",           "color": "#f59e0b"},
    # 3. Tempat (Fisik/Spesifik seperti kampung/candi/jalan/gunung)
    "_PLACE_ID":   {"label": "Tempat",              "icon": "fa-map-pin",        "color": "#22d3ee"},
    # 4. Organisasi
    "ORG":         {"label": "Organisasi",          "icon": "fa-building",       "color": "#0ea5e9"},
    # 5. Waktu
    "TIME":        {"label": "Waktu",               "icon": "fa-clock",          "color": "#ec4899"},
    # 6. Hari
    "_DAY_ID":     {"label": "Hari",                "icon": "fa-calendar-day",   "color": "#f43f5e"},
    # 7. Tanggal
    "DATE":        {"label": "Tanggal",             "icon": "fa-calendar-alt",   "color": "#8b5cf6"},
    # 8. Urutan
    "ORDINAL":     {"label": "Urutan",              "icon": "fa-list-ol",        "color": "#64748b"},
    # 9. Persentase
    "PERCENT":     {"label": "Persentase",          "icon": "fa-percent",        "color": "#f97316"},
    # 10. Uang
    "MONEY":       {"label": "Uang",                "icon": "fa-coins",          "color": "#eab308"},
    # 11. Jumlah
    "QUANTITY":    {"label": "Jumlah",              "icon": "fa-scale-balanced", "color": "#14b8a6"},
    # 12. Bilangan
    "CARDINAL":    {"label": "Bilangan",            "icon": "fa-hashtag",        "color": "#94a3b8"},
    # 13. Peristiwa
    "EVENT":       {"label": "Peristiwa",           "icon": "fa-star",           "color": "#a855f7"},
    # 14. Cuaca
    "_WEATHER_ID": {"label": "Cuaca",               "icon": "fa-cloud-sun",      "color": "#38bdf8"},
    # 15. Produk
    "PRODUCT":     {"label": "Produk",              "icon": "fa-box",            "color": "#fb923c"},
    # 16. Kegiatan
    "_ACTIVITY_ID":{"label": "Kegiatan",            "icon": "fa-running",        "color": "#10b981"},
}


# ── Kata kunci penanda Indonesia dengan inline (?i:...) ────────
_TEMPAT_PREFIX = r"\b(?i:kampung|desa|kelurahan|kecamatan|kabupaten|kota|provinsi|gunung|pantai|sungai|danau|pulau|jalan|jl|gang|gg|kompleks?|perumahan|pasar|candi|masjid|gereja|pura|vihara|stadion|taman|stasiun|bandara|pelabuhan|dusun|benua|teluk|selat|bukit)\b"
_ORG_PREFIX    = r"\b(?i:pt|cv|kementerian|dinas|yayasan|universitas|univ|institut|sekolah|sma|smp|sd|pemerintah|pemprov|pemkot|komite|asosiasi|badan|lembaga|organisasi|perusahaan|bank|maspion|pertamina|pln|telkom)\b"
_PERSON_PREFIX = r"\b(?i:bapak|ibu|pak|bu|mas|mbak|kakak|kak|adik|om|tante|tuan|nyonya|nona|dr|prof|ir|drs|haji|h|hj|ustadz?|kyai)\b"

# Kata umum Indonesia yang bukan entitas proper noun
BLACKLIST = {
    "yang", "dan", "di", "ke", "dari", "untuk", "dengan", "pada", "adalah", 
    "ini", "itu", "ada", "sudah", "akan", "juga", "atau", "karena", "saat", 
    "ketika", "setelah", "sebelum", "selama", "antara", "oleh", "dalam",
    "sebagai", "bahwa", "mereka", "kita", "kami", "dia", "ia", "kamu",
    "the", "a", "an", "of", "in", "on", "at", "to", "for"
}

# Kata lowercase yang diizinkan berada di dalam nama entitas proper noun
_ALLOWED_LOWERCASE_WORDS = {
    "dan", "di", "ke", "dari", "yang", "untuk", "bin", "binti",
    "of", "in", "and", "the", "at", "on", "with", "a", "an", "de", "van"
}

# Kamus kata umum awal kalimat Bahasa Indonesia (Bukan nama orang/proper noun)
# Mencegah kata pertama dari kalimat yang salah dideteksi spaCy lolos sebagai Orang.
_COMMON_INDONESIAN_START_WORDS = {
    "hasil", "sebelum", "setelah", "pagi", "udara", "hari", "sorak-sorai", "penonton",
    "nasihat", "persaingan", "beberapa", "ketika", "pelatih", "pelari", "garis", "sejak",
    "langit", "embun", "perlombaan", "kecepatan", "teman-teman", "teman", "perjalanan",
    "sore", "malam", "siang", "pagi", "besok", "kemarin", "tahun", "bulan", "minggu",
    "waktu", "saat", "kala", "masa", "kegiatan", "acara", "awal", "akhir", "dalam",
    "luar", "atas", "bawah", "samping", "tengah", "depan", "belakang", "semua", "setiap",
    "banyak", "sedikit", "beberapa", "seluruh", "sebagian", "salah", "benar", "baik",
    "buruk", "baru", "lama", "tua", "muda", "besar", "kecil", "tinggi", "rendah",
    "panjang", "pendek", "jauh", "dekat", "cepat", "lambat", "kuat", "lemah",
    "adalah", "merupakan", "yaitu", "yakni", "ialah", "bahwa", "sebagai", "dengan",
    "dan", "atau", "tetapi", "namun", "melainkan", "sedangkan", "padahal", "sambil",
    "mereka", "kita", "kami", "dia", "ia", "kamu", "saya", "anda", "kalian", "beliau",
    "pagi-pagi", "malam-malam", "siang-siang", "secepat", "selambat", "sebaik", "seburuk",
    "sang", "para", "si", "seorang", "suatu", "sebuah",
}

# ── Pola Regex Khusus Bahasa Indonesia (Case-sensitive untuk nama entitas) ─
_REGEX_RULES = [
    # 1. HARI (misal: "Hari Senin", "Senin pagi", "Jumat malam", "Minggu")
    (re.compile(r"\b(?i:Senin|Selasa|Rabu|Kamis|Jum'?at|Sabtu|Minggu)\b", re.U), "_DAY_ID"),
    
    # 2. CUACA (misal: "hujan lebat", "cuaca cerah", "langit mendung", "panas", "dingin")
    (re.compile(r"\b(?i:hujan|cerah|mendung|berawan|badai|gerimis|panas|dingin|berangin)\b", re.U), "_WEATHER_ID"),

    # 3. KEGIATAN (misal: "Perlombaan Lari", "Festival Batik", "Upacara Bendera")
    (re.compile(r"\b(?i:perlombaan|pertandingan|upacara|festival|konser|seminar|rapat|kegiatan)\s+([A-Z][a-zA-Z0-9]*(?:\s+[A-Z][a-zA-Z0-9]*)*)", re.U), "_ACTIVITY_ID"),

    # 4. TEMPAT / LOKASI (misal: "Kampung Batik Laweyan", "Kota Solo", "Jalan Sudirman")
    (re.compile(rf"{_TEMPAT_PREFIX}\s+([A-Z][a-zA-Z0-9]*(?:\s+[A-Z][a-zA-Z0-9]*)*)", re.U), "_PLACE_ID"),
    
    # 5. ORGANISASI (misal: "PT Sukses Makmur", "Yayasan Pendidikan Jaya", "Universitas Indonesia")
    (re.compile(rf"{_ORG_PREFIX}\s+([A-Z][a-zA-Z0-9&]*(?:\s+[A-Z][a-zA-Z0-9&]*)*)", re.U), "ORG"),
    
    # 6. NAMA ORANG (misal: "Pak Jokowi", "Ibu Megawati", "dr. Andi")
    (re.compile(rf"{_PERSON_PREFIX}\s+([A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)*)", re.U), "PERSON"),
    
    # 7. TANGGAL INDONESIA (misal: "5 Juli 2026", "21 Maret 1999", "17 Agustus 1945")
    (re.compile(r"\b\d{1,2}\s+(?i:Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember)\s+\d{4}\b"), "DATE"),
    
    # 8. UANG RUPIAH (misal: "Rp 50.000", "Rp1.500.000", "Rp. 10.000.000")
    (re.compile(r"\b(?i:Rp)\.?\s?\d{1,3}(?:\.\d{3})*(?:,\d{2})?\b"), "MONEY"),
]


def _is_valid_proper_noun(text: str) -> bool:
    """
    Memastikan bahwa entitas proper noun (Orang, Organisasi, Tempat, Lokasi, dll.)
    tidak mengandung kata-kata lowercase umum bahasa Indonesia.
    """
    words = text.split()
    if not words:
        return False
        
    # Kata pertama wajib diawali huruf kapital atau digit
    if not (words[0][0].isupper() or words[0][0].isdigit()):
        return False
        
    for word in words[1:]:
        cleaned = re.sub(r'^[^\w]+|[^\w]+$', '', word)
        if not cleaned:
            continue
            
        # Abaikan kata hubung/preposisi lowercase yang diizinkan
        if cleaned.lower() in _ALLOWED_LOWERCASE_WORDS:
            continue
            
        # Wajib diawali huruf kapital atau digit
        if not (cleaned[0].isupper() or cleaned[0].isdigit()):
            return False
            
    return True


def _clean_extracted_text(text: str, label: str) -> str:
    """
    Membersihkan kata-kata sampah di akhir entitas yang sering ditangkap spaCy.
    """
    words = text.split()
    if not words:
        return text

    # Jika kata terakhir adalah kata umum Indonesia, potong
    while len(words) > 1 and words[-1].lower() in BLACKLIST:
        words.pop()

    # Bersihkan jika spaCy menangkap kata kerja di akhir nama orang
    if label == "PERSON" and len(words) > 1:
        if words[-1].lower() in {"mengunjungi", "berkunjung", "pernah", "ke", "adalah", "melakukan", "mengatakan", "menilai", "membuat"}:
            words.pop()

    return " ".join(words)


def extract_entities(text: str) -> list:
    """
    Ekstrak entitas bernama menggunakan metode hybrid (spaCy + Regex Aturan Indonesia).
    """
    seen = set()
    raw_entities = []

    # ─────────────────────────────────────────────────────────
    # LANGKAH 1: Ekstraksi Berbasis Aturan Regex Indonesia (Prioritas Tinggi)
    # ─────────────────────────────────────────────────────────
    for pattern, label_key in _REGEX_RULES:
        for match in pattern.finditer(text):
            ent_text = match.group(0).strip()
            ent_text = _clean_extracted_text(ent_text, label_key)
            if len(ent_text) < 2 or ent_text.lower() in BLACKLIST:
                continue

            raw_entities.append({
                "text": ent_text,
                "label_key": label_key,
                "priority": True,
            })

    # ─────────────────────────────────────────────────────────
    # LANGKAH 2: Ekstraksi Berbasis spaCy (Untuk data sisa/Bahasa Inggris)
    # ─────────────────────────────────────────────────────────
    nlp = _load_model()
    if nlp is not None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            doc = nlp(text[:6000])

        for ent in doc.ents:
            label_key = ent.label_
            ent_text = ent.text.strip()

            # Normalisasi label spacy ke kategori internal kita
            if label_key == "GPE":
                label_key = "GPE"       # Lokasi
            elif label_key in ("LOC", "FAC"):
                label_key = "_PLACE_ID" # Tempat
            elif label_key == "DATE":
                if any(day in ent_text.lower() for day in ["senin", "selasa", "rabu", "kamis", "jumat", "sabtu", "minggu"]):
                    continue
                label_key = "DATE"

            if label_key not in LABEL_MAP:
                continue

            ent_text = _clean_extracted_text(ent_text, label_key)

            # ── LOGIKA DEKONSTRUKSI PINTAR UNTUK PERSON YANG KOTOR ──
            # Jika spaCy mendeteksi kalimat panjang sebagai PERSON, kita bedah dan ambil kata pertamanya saja
            # (Misal: "Raka merasa beruntung..." -> kita ambil "Raka")
            if label_key == "PERSON" and not _is_valid_proper_noun(ent_text):
                words = ent_text.split()
                if words:
                    first_word = re.sub(r'^[^\w]+|[^\w]+$', '', words[0])
                    # Pastikan kata pertama diawali huruf kapital, panjang >= 2, dan bukan kata umum Indonesia
                    if (len(first_word) >= 2 and 
                        first_word[0].isupper() and 
                        first_word.lower() not in BLACKLIST and 
                        first_word.lower() not in _COMMON_INDONESIAN_START_WORDS):
                        ent_text = first_word
                    else:
                        continue
            
            # Validasi huruf kapital/proper noun untuk entitas berbasis teks
            if label_key in {"PERSON", "ORG", "GPE", "_PLACE_ID", "EVENT", "PRODUCT", "_ACTIVITY_ID"}:
                if not _is_valid_proper_noun(ent_text):
                    continue

            # Validasi digit untuk tipe angka
            if label_key in {"PERCENT", "MONEY", "QUANTITY", "CARDINAL"}:
                if not any(c.isdigit() for c in ent_text):
                    continue

            if len(ent_text) < 2 or ent_text.lower() in BLACKLIST:
                continue

            # Koreksi label manual jika spaCy salah mendeteksinya
            words_lower = [w.lower() for w in ent_text.split()]
            has_place_prefix = any(w in {"kampung", "desa", "jalan", "jl", "kota", "kabupaten", "provinsi", "gunung"} for w in words_lower)
            has_org_prefix   = any(w in {"pt", "cv", "yayasan", "universitas", "sekolah"} for w in words_lower)

            if label_key == "PERSON":
                if has_place_prefix:
                    label_key = "_PLACE_ID"
                elif has_org_prefix:
                    label_key = "ORG"
                else:
                    if any(w in {"mengunjungi", "adalah", "pernah", "melakukan", "ke", "di", "dari", "berlatih", "merasa"} for w in words_lower):
                        continue

            raw_entities.append({
                "text": ent_text,
                "label_key": label_key,
                "priority": False,
            })

    # ─────────────────────────────────────────────────────────
    # LANGKAH 3: Penyaringan Overlap & Deduplikasi Cerdas
    # ─────────────────────────────────────────────────────────
    raw_entities.sort(key=lambda x: (not x["priority"], -len(x["text"])))

    filtered_entities = []
    for candidate in raw_entities:
        cand_text = candidate["text"]
        cand_lbl  = candidate["label_key"]

        overlap = False
        for accepted in filtered_entities:
            if cand_text.lower() in accepted["text"].lower() or accepted["text"].lower() in cand_text.lower():
                overlap = True
                break
        
        if not overlap:
            filtered_entities.append(candidate)

    # ─────────────────────────────────────────────────────────
    # LANGKAH 4: Konversi ke Format Hasil
    # ─────────────────────────────────────────────────────────
    final_list = []
    for item in filtered_entities:
        label_key = item["label_key"]
        ent_text  = item["text"]
        
        key = (ent_text.lower(), label_key)
        if key not in seen:
            seen.add(key)
            meta = LABEL_MAP[label_key]
            final_list.append({
                "text": ent_text,
                "label": meta["label"],
                "icon": meta["icon"],
                "color": meta["color"],
                "_order": list(LABEL_MAP.keys()).index(label_key),
            })

    # Urutkan berdasarkan urutan kategori di LABEL_MAP
    final_list.sort(key=lambda x: x["_order"])

    for item in final_list:
        del item["_order"]

    return final_list[:30]
