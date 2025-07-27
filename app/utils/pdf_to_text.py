
import PyPDF2

def extract_pdf_text(file_stream):
    try:
        reader = PyPDF2.PdfReader(file_stream)
        full_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
        return full_text
    except Exception as e:
        raise Exception(f"Failed to extract PDF text: {e}")
