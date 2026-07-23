from docx import Document


def read_docx(path):

    doc = Document(path)

    text = "\n".join(

        para.text

        for para in
        doc.paragraphs

    )

    return text

