import nltk

nltk.download(
    "punkt",
    quiet=True
)

from nltk.tokenize import word_tokenize


def tokenize_text(text):

    return word_tokenize(text)

