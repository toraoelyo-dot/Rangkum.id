
import re


def clean_text(text):
    """
    Membersihkan teks untuk keperluan analisis NLP umum
    (keyword extraction, summarization, topic classification, complexity).
    Teks dikecilkan hurufnya agar konsisten.
    """

    # Hilangkan spasi berlebih
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    # Hilangkan karakter selain huruf, angka, spasi, dan tanda baca dasar
    text = re.sub(
        r"[^\w\s.,!?]",
        "",
        text
    )

    return text.strip()


def clean_text_preserve_case(text):
    """
    Membersihkan teks TANPA mengubah huruf kapital.
    Digunakan untuk analisis sentimen dan NER yang sensitif terhadap kapitalisasi.
    """

    # Hilangkan spasi berlebih
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    # Hilangkan karakter tidak perlu tapi pertahankan kapitalisasi
    text = re.sub(
        r"[^\w\s.,!?'\"-]",
        "",
        text
    )

    return text.strip()
