from PyPDF2 import PdfReader


def read_pdf(path):

    reader = PdfReader(path)

    text = ""

    for page in reader.pages:

        extracted = page.extract_text()

        if extracted:

            text += extracted + " "

    return text

