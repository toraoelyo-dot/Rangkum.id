from flask import (
    Flask,
    render_template,
    request,
    redirect,
    flash
)

import os
import warnings

# Suppress FutureWarning dari transformers & UserWarning dari spaCy
warnings.filterwarnings("ignore", category=FutureWarning, module="transformers")
warnings.filterwarnings("ignore", category=UserWarning,   module="spacy")
warnings.filterwarnings("ignore", category=UserWarning,   module="torch")

# ==========================
# PREPROCESSING
# ==========================

from preprocessing.cleaner import (
    clean_text,
    clean_text_preserve_case
)

# ==========================
# MODELS
# ==========================

from models.summarizer import summarize_document
from models.keyword_extractor import extract_keywords
from models.sentiment import analyze_sentiment
from models.classifier import classify_topic
from models.ner import extract_entities
from models.complexity import complexity_score

# ==========================
# FILE UTILITIES
# ==========================

from utils.pdf_reader import read_pdf
from utils.docx_reader import read_docx
from utils.file_handler import (
    allowed_file,
    document_statistics
)
from utils.db_handler import (
    init_db,
    save_history,
    get_all_history,
    get_history_by_id,
    delete_history,
    clear_all_history,
    update_wordcloud_availability
)
# ==========================
# WORD CLOUD
# ==========================

from wordcloud import WordCloud
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ==========================
# FLASK APP
# ==========================

app = Flask(__name__)
app.secret_key = "smartdoc_secret_key"

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Inisialisasi database SQLite & direktori khusus Word Cloud
init_db()
os.makedirs(os.path.join(app.root_path, "static", "uploads", "wordclouds"), exist_ok=True)

# ==========================
# HELPER: GENERATE WORD CLOUD
# ==========================

def generate_wordcloud(text, filename="wordcloud.png"):
    wordcloud = WordCloud(
        width=900,
        height=450,
        background_color="black",
        colormap="plasma",
        max_words=80,
        min_font_size=10,
        collocations=False,
    ).generate(text)

    output_path = os.path.join(
        app.root_path, "static", "uploads", "wordclouds", filename
    )

    plt.figure(figsize=(10, 5), facecolor="black")
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.tight_layout(pad=0)
    plt.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close()

# ==========================
# HELPER: PROSES TEKS & RENDER
# ==========================

def process_and_render(raw_text: str, title: str):
    """
    Fungsi inti: bersihkan → analisis NLP → simpan ke database → redirect ke hasil.
    Digunakan oleh route upload file maupun input teks langsung.
    """
    if len(raw_text.strip()) < 50:
        flash("Teks terlalu pendek. Minimal 50 karakter diperlukan.")
        return redirect("/")

    # Teks lowercase untuk summarizer/keyword/topic/complexity
    cleaned_text  = clean_text(raw_text)
    # Teks asli (kapitalisasi dijaga) untuk sentimen & NER
    original_text = clean_text_preserve_case(raw_text)

    word_count = len(cleaned_text.split())

    if word_count > 5000:
        flash("Teks terlalu panjang. Maksimum 5000 kata untuk dianalisis.")
        return redirect("/")

    # ── NLP Pipeline ──
    summary    = summarize_document(cleaned_text)
    keywords   = extract_keywords(cleaned_text)
    topic      = classify_topic(cleaned_text)
    sentiment  = analyze_sentiment(original_text)
    entities   = extract_entities(original_text)
    complexity = complexity_score(cleaned_text)

    # ── Kelompokkan entitas berdasarkan label ──
    from collections import OrderedDict
    entity_groups = OrderedDict()
    for ent in entities:
        lbl = ent["label"]
        if lbl not in entity_groups:
            entity_groups[lbl] = {
                "label": lbl,
                "icon":  ent["icon"],
                "color": ent["color"],
                "items": [],
            }
        entity_groups[lbl]["items"].append(ent["text"])
    grouped_entities = list(entity_groups.values())

    # ── Statistik ──
    stats        = document_statistics(cleaned_text)
    reading_time = max(1, round(stats["word_count"] / 200))

    # ── Simpan ke database ──
    history_id = save_history(
        title=title,
        summary=summary,
        keywords=keywords,
        topic=topic,
        sentiment=sentiment,
        complexity=complexity,
        stats=stats,
        reading_time=reading_time,
        grouped_entities=grouped_entities,
        wordcloud_available=False
    )

    # ── Word Cloud ──
    try:
        generate_wordcloud(cleaned_text, filename=f"wordcloud_{history_id}.png")
        update_wordcloud_availability(history_id, True)
    except Exception as e:
        print(f"Gagal membuat Word Cloud: {e}")
        update_wordcloud_availability(history_id, False)

    return redirect(f"/result/{history_id}")


# ==========================
# HOME PAGE
# ==========================

@app.route("/")
def home():
    history_list = get_all_history()
    return render_template("index.html", history=history_list)


# ==========================
# RESULT DETAIL PAGE
# ==========================

@app.route("/result/<int:history_id>")
def result_detail(history_id):
    data = get_history_by_id(history_id)
    if not data:
        flash("Riwayat analisis tidak ditemukan.")
        return redirect("/")
        
    return render_template(
        "result.html",
        id=data["id"],
        title=data["title"],
        created_at=data["created_at"],
        summary=data["summary"],
        keywords=data["keywords"],
        topic=data["topic"],
        sentiment=data["sentiment"],
        grouped_entities=data["grouped_entities"],
        complexity=data["complexity"],
        reading_time=data["reading_time"],
        stats=data["stats"],
        wordcloud_available=bool(data["wordcloud_available"]),
    )


# ==========================
# DELETE HISTORY
# ==========================

@app.route("/history/delete/<int:history_id>", methods=["POST"])
def delete_history_route(history_id):
    data = get_history_by_id(history_id)
    if data:
        # Hapus file Word Cloud jika ada
        wordcloud_filename = f"wordcloud_{history_id}.png"
        wordcloud_path = os.path.join(app.root_path, "static", "uploads", "wordclouds", wordcloud_filename)
        if os.path.exists(wordcloud_path):
            try:
                os.remove(wordcloud_path)
            except Exception as e:
                print(f"Error removing wordcloud file: {e}")
                
        # Hapus file upload asli jika ada di folder uploads
        if data["title"] != "Teks Input":
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], data["title"])
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except Exception as e:
                    print(f"Error removing original uploaded file: {e}")
                    
        delete_history(history_id)
        flash("Riwayat analisis berhasil dihapus.")
    else:
        flash("Riwayat tidak ditemukan.")
        
    return redirect("/")


# ==========================
# CLEAR ALL HISTORY
# ==========================

@app.route("/history/clear", methods=["POST"])
def clear_all_history_route():
    history_list = get_all_history()
    for item in history_list:
        history_id = item["id"]
        # Hapus berkas Word Cloud
        wordcloud_filename = f"wordcloud_{history_id}.png"
        wordcloud_path = os.path.join(app.root_path, "static", "uploads", "wordclouds", wordcloud_filename)
        if os.path.exists(wordcloud_path):
            try:
                os.remove(wordcloud_path)
            except Exception as e:
                print(f"Error removing wordcloud file: {e}")
                
        # Hapus file upload asli
        if item["title"] != "Teks Input":
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], item["title"])
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except Exception as e:
                    print(f"Error removing original uploaded file: {e}")
                    
    clear_all_history()
    flash("Semua riwayat analisis berhasil dibersihkan.")
    return redirect("/")


# ==========================
# ANALYZE — UPLOAD FILE
# ==========================

@app.route("/analyze", methods=["POST"])
def analyze():

    file = request.files.get("file")

    if not file or file.filename == "":
        flash("Tidak ada file yang dipilih.")
        return redirect("/")

    if not allowed_file(file.filename):
        flash("Hanya file PDF, DOCX, dan TXT yang diizinkan.")
        return redirect("/")

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"], file.filename
    )
    file.save(filepath)

    extension = file.filename.split(".")[-1].lower()
    raw_text  = ""

    try:
        if extension == "pdf":
            raw_text = read_pdf(filepath)
        elif extension == "docx":
            raw_text = read_docx(filepath)
        elif extension == "txt":
            with open(filepath, "r", encoding="utf-8") as f:
                raw_text = f.read()
    except Exception as e:
        flash(f"Gagal membaca file: {e}")
        return redirect("/")

    return process_and_render(raw_text, title=file.filename)

# ==========================
# ANALYZE — INPUT TEKS LANGSUNG
# ==========================

@app.route("/analyze-text", methods=["POST"])
def analyze_text():
    raw_text = request.form.get("text_input", "").strip()

    if not raw_text:
        flash("Teks tidak boleh kosong.")
        return redirect("/")

    return process_and_render(raw_text, title="Teks Input")

# ==========================
# RUN APP
# ==========================

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)