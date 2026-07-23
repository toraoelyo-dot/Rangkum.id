from collections import Counter

from nltk.corpus import stopwords

import nltk

nltk.download(
    "stopwords",
    quiet=True
)


def extract_frequent_words(
    text,
    top_n=10
):

    stop_words = set(
        stopwords.words(
            "english"
        )
    )

    words = [

        word

        for word in
        text.split()

        if word not in stop_words

    ]

    return Counter(
        words
    ).most_common(
        top_n
    )
