# PDF to Text Streamlit Project

Streamlit tabanlı PDF dosyalarından metin çıkarma web uygulaması.

<video controls src="pdf2text.mp4" title="Title"></video>

## Desteklenen Yöntemler

**PyMuPDF (fitz)**
- Tüm Metin
- Belirli Sayfa
- Markdown/JSON Çıktısı
- Metin Arama
- Tablo Tespiti
- Görüntü Çıkarma

**PDFplumber**
- Tüm Metin
- Belirli Sayfa
- Tablo Çıkarma
- Görüntü Çıkarma

**Camelot (Sadece Tablolar)**
- Tablo çıkarma için Lattice algoritması

**Unstructured (Hızlı Strateji)**
- Sayfa kesimleri ile opsiyonel hızlı metin çıkarma

**OCR Teknolojileri**
- PaddleOCR
- img2table (Tablo Tespiti)
- PDFplumber (Tablo Çıkarma)
- Donut (Belge Analizi)
- LayoutParser (Layout Analizi)

## Kurulum

```bash
git clone https://github.com/Serkan0YLDZ/pdf2text-streamlit.git
cd pdf2text-streamlit
python -m venv myenv
source myenv/bin/activate  # Linux/Mac
# veya
myenv\Scripts\activate  # Windows
pip install -r requirements.txt
streamlit run main.py
```

## Önemli Notlar

- NumPy 2.x sürümleri desteklenmemektedir (NumPy < 2.0 kullanın)
- OpenCV 4.9.0'dan düşük sürümler kullanılmalıdır
- PyTorch 2.2.0+cpu ve Transformers 4.37.0 uyumlu sürümlerdir
- deepdoctection kütüphanesi uyumsuzluk nedeniyle kaldırılmıştır

## Kullanım

1. Ana sayfada PDF dosyanızı yükleyin
2. "Direct Text Extraction" sekmesinde metin çıkarma yöntemini seçin
3. "OCR Text Extraction" sekmesinde OCR teknolojilerini kullanın
4. Sonuçları görüntüleyin ve indirin