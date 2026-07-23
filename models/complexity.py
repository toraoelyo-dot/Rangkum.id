def complexity_score(text):

    words = text.split()

    if len(words) == 0:

        return "Tidak Diketahui"

    avg_word_length = (

        sum(

            len(word)

            for word
            in words

        )

        / len(words)

    )

    if avg_word_length < 5:

        return "Mudah"

    elif avg_word_length < 7:

        return "Sedang"

    else:

        return "Sulit"
