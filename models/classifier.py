
from transformers import pipeline


classifier = pipeline(
    "zero-shot-classification",
    model="facebook/bart-large-mnli"
)


def classify_topic(text):
    # Gunakan label dalam bahasa Inggris agar model zero-shot BART (yang berbasis bahasa Inggris)
    # dapat mengklasifikasikan dengan akurasi tinggi, lalu petakan hasilnya ke bahasa Indonesia.
    label_mapping = {
        "technology": "Teknologi",
        "business": "Bisnis",
        "sports": "Olahraga",
        "politics": "Politik",
        "health": "Kesehatan",
        "education": "Pendidikan",
        "entertainment": "Hiburan"
    }

    english_labels = list(label_mapping.keys())

    result = classifier(
        text[:1000],
        english_labels
    )

    best_english_label = result["labels"][0]
    return label_mapping[best_english_label]

