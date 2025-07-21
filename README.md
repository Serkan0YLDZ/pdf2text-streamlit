# PDF to Text Streamlit Project

Streamlit based web application for extracting text from PDF files.

<video controls src="pdf2text.mp4" title="Title"></video>

## Supported Methods

**PyMuPDF (fitz)**
- All Text
- Specific Page
- Markdown/JSON Output
- Search Text
- Table Detection
- Image Extraction

**PDFplumber**
- All Text
- Specific Page
- Table Extraction
- Image Extraction

**Camelot (Tables Only)**
- Lattice algorithm for table extraction

**Unstructured (Fast Strategy)**
- Fast text extraction with optional page breaks

## Installation

```bash
git clone https://github.com/Serkan0YLDZ/pdf2text-streamlit.git
cd pdf2text-streamlit
pip install -r requirements.txt
streamlit run main.py
```