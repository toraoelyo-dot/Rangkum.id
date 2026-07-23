ALLOWED_EXTENSIONS = {
    "pdf",
    "docx",
    "txt"
}


def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(
            ".",
            1
        )[1].lower()
        in ALLOWED_EXTENSIONS
    )


def document_statistics(text):

    words = text.split()

    return {

        "word_count":
        len(words),

        "sentence_count":
        len(
            text.split(".")
        ),

        "character_count":
        len(text)

    }
