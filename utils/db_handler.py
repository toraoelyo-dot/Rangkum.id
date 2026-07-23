import sqlite3
import json
import os

DB_NAME = "rangkum_history.db"

def get_db_connection(db_path=DB_NAME):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path=DB_NAME):
    """Menginisialisasi tabel database jika belum ada."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            summary TEXT NOT NULL,
            keywords TEXT, -- JSON string
            topic TEXT,
            sentiment_label TEXT,
            sentiment_score REAL,
            sentiment_color TEXT,
            sentiment_icon TEXT,
            complexity TEXT,
            reading_time INTEGER,
            word_count INTEGER,
            sentence_count INTEGER,
            character_count INTEGER,
            grouped_entities TEXT, -- JSON string
            wordcloud_available INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def save_history(title, summary, keywords, topic, sentiment, complexity, stats, reading_time, grouped_entities, wordcloud_available, db_path=DB_NAME):
    """Menyimpan entri riwayat analisis baru dan mengembalikan ID-nya."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    # Konversi list/dict ke JSON string
    keywords_json = json.dumps(keywords)
    grouped_entities_json = json.dumps(grouped_entities)
    
    cursor.execute("""
        INSERT INTO history (
            title, summary, keywords, topic, 
            sentiment_label, sentiment_score, sentiment_color, sentiment_icon,
            complexity, reading_time, word_count, sentence_count, character_count,
            grouped_entities, wordcloud_available
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        title,
        summary,
        keywords_json,
        topic,
        sentiment.get("label", "Netral") if isinstance(sentiment, dict) else "Netral",
        sentiment.get("score", 0.0) if isinstance(sentiment, dict) else 0.0,
        sentiment.get("color", "#94a3b8") if isinstance(sentiment, dict) else "#94a3b8",
        sentiment.get("icon", "fa-face-meh") if isinstance(sentiment, dict) else "fa-face-meh",
        complexity,
        reading_time,
        stats.get("word_count", 0) if isinstance(stats, dict) else 0,
        stats.get("sentence_count", 0) if isinstance(stats, dict) else 0,
        stats.get("character_count", 0) if isinstance(stats, dict) else 0,
        grouped_entities_json,
        1 if wordcloud_available else 0
    ))
    
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id

def get_all_history(db_path=DB_NAME):
    """Mengambil daftar ringkas seluruh riwayat analisis, terurut dari yang terbaru."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, created_at, word_count, topic, sentiment_label, complexity 
        FROM history 
        ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    
    # Ubah Row object ke dict
    history_list = []
    for row in rows:
        history_list.append(dict(row))
    return history_list

def get_history_by_id(history_id, db_path=DB_NAME):
    """Mengambil entri riwayat lengkap berdasarkan ID-nya."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM history WHERE id = ?", (history_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row is None:
        return None
        
    data = dict(row)
    # De-serialisasi JSON strings
    try:
        data["keywords"] = json.loads(data["keywords"]) if data["keywords"] else []
    except Exception:
        data["keywords"] = []
        
    try:
        data["grouped_entities"] = json.loads(data["grouped_entities"]) if data["grouped_entities"] else []
    except Exception:
        data["grouped_entities"] = []
        
    # Buat dict sentiment & stats agar kompatibel dengan view yang ada
    data["sentiment"] = {
        "label": data["sentiment_label"],
        "score": data["sentiment_score"],
        "color": data["sentiment_color"],
        "icon": data["sentiment_icon"]
    }
    
    data["stats"] = {
        "word_count": data["word_count"],
        "sentence_count": data["sentence_count"],
        "character_count": data["character_count"]
    }
    
    return data

def delete_history(history_id, db_path=DB_NAME):
    """Menghapus entri riwayat berdasarkan ID."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM history WHERE id = ?", (history_id,))
    conn.commit()
    conn.close()

def clear_all_history(db_path=DB_NAME):
    """Menghapus seluruh data dari tabel history."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM history")
    conn.commit()
    conn.close()

def update_wordcloud_availability(history_id, available, db_path=DB_NAME):
    """Memperbarui status ketersediaan Word Cloud untuk riwayat tertentu."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE history SET wordcloud_available = ? WHERE id = ?", (1 if available else 0, history_id))
    conn.commit()
    conn.close()
