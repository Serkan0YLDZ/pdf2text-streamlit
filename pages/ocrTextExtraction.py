import os
import streamlit as st
from streamlit_pdf_viewer import pdf_viewer
import fitz
import pandas as pd
import numpy as np
from PIL import Image
import io
import base64

# OCR ve tablo çıkarma kütüphaneleri için import'lar
try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False

try:
    import img2table
    from img2table.document import Image as Img2TableImage
    from img2table.ocr import PaddleOCR as Img2TablePaddleOCR
    IMG2TABLE_AVAILABLE = True
except ImportError:
    IMG2TABLE_AVAILABLE = False

# deepdoctection kaldırıldı - uyumsuzluk nedeniyle
DEEPDOCTECTION_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    from transformers import DonutProcessor, VisionEncoderDecoderModel
    import torch
    DONUT_AVAILABLE = True
except ImportError:
    DONUT_AVAILABLE = False

try:
    import layoutparser as lp
    LAYOUTPARSER_AVAILABLE = True
except ImportError:
    LAYOUTPARSER_AVAILABLE = False

def extract_images_from_pdf(file_path):
    """PDF'den görüntüleri çıkarır"""
    doc = fitz.open(file_path)
    images = []
    
    for page_num in range(doc.page_count):
        page = doc[page_num]
        image_list = page.get_images()
        
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            
            # PIL Image'e çevir
            pil_image = Image.open(io.BytesIO(image_bytes))
            images.append({
                'page': page_num + 1,
                'image': pil_image,
                'ext': image_ext,
                'index': img_index
            })
    
    doc.close()
    return images

def paddleocr_extraction(image):
    """PaddleOCR ile metin çıkarma"""
    if not PADDLEOCR_AVAILABLE:
        return "PaddleOCR kütüphanesi yüklü değil. 'pip install paddlepaddle paddleocr' komutu ile yükleyin."
    
    try:
        ocr = PaddleOCR(use_angle_cls=True, lang='en')
        result = ocr.ocr(np.array(image))
        
        extracted_text = ""
        for line in result:
            if line:
                for word_info in line:
                    if word_info:
                        text = word_info[1][0]
                        confidence = word_info[1][1]
                        extracted_text += f"{text} (Confidence: {confidence:.2f})\n"
        
        return extracted_text if extracted_text else "Metin bulunamadı"
    except Exception as e:
        return f"PaddleOCR hatası: {str(e)}"

def img2table_extraction(image):
    """img2table ile tablo çıkarma"""
    if not IMG2TABLE_AVAILABLE:
        return "img2table kütüphanesi yüklü değil. 'pip install img2table' komutu ile yükleyin."
    
    try:
        # PIL Image'i numpy array'e çevir
        img_array = np.array(image)
        
        # OCR engine olarak PaddleOCR kullan
        ocr = Img2TablePaddleOCR()
        
        # Image2Table ile tablo tespiti
        img = Img2TableImage(img_array)
        tables = img.extract_tables(ocr=ocr)
        
        if tables:
            result = f"Bulunan tablo sayısı: {len(tables)}\n\n"
            for i, table in enumerate(tables):
                result += f"--- Tablo {i+1} ---\n"
                result += str(table) + "\n\n"
            return result
        else:
            return "Tablo bulunamadı"
    except Exception as e:
        return f"img2table hatası: {str(e)}"

def deepdoctection_extraction(image):
    """deepdoctection ile belge analizi - KULLANILAMIYOR"""
    return "deepdoctection kütüphanesi uyumsuzluk nedeniyle kaldırıldı."

def pdfplumber_extraction(file_path):
    """PDFplumber ile tablo çıkarma"""
    if not PDFPLUMBER_AVAILABLE:
        return "PDFplumber kütüphanesi yüklü değil. 'pip install pdfplumber' komutu ile yükleyin."
    
    try:
        with pdfplumber.open(file_path) as pdf:
            all_tables = []
            
            for page_num, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                if tables:
                    for table_index, table in enumerate(tables):
                        if table and len(table) > 0:
                            all_tables.append({
                                'page': page_num + 1,
                                'table_index': table_index + 1,
                                'data': table
                            })
            
            if all_tables:
                result = f"PDFplumber ile bulunan tablo sayısı: {len(all_tables)}\n\n"
                for table_info in all_tables:
                    result += f"--- Sayfa {table_info['page']} - Tablo {table_info['table_index']} ---\n"
                    
                    # DataFrame oluştur
                    table_data = table_info['data']
                    if table_data[0]:
                        columns = []
                        for j, col in enumerate(table_data[0]):
                            if col is None or col == "":
                                columns.append(f"Sütun_{j+1}")
                            else:
                                columns.append(str(col))
                        
                        # Tekrarlanan sütun isimlerini düzelt
                        seen = {}
                        unique_columns = []
                        for col in columns:
                            if col in seen:
                                seen[col] += 1
                                unique_columns.append(f"{col}_{seen[col]}")
                            else:
                                seen[col] = 0
                                unique_columns.append(col)
                        
                        df = pd.DataFrame(table_data[1:], columns=unique_columns)
                        result += f"Tablo boyutu: {df.shape}\n"
                        result += str(df.head()) + "\n\n"
                    else:
                        result += "Tablo verisi boş\n\n"
                
                return result
            else:
                return "PDFplumber ile tablo bulunamadı"
    except Exception as e:
        return f"PDFplumber hatası: {str(e)}"

def donut_extraction(image):
    """Donut model ile belge analizi"""
    if not DONUT_AVAILABLE:
        return "Donut kütüphanesi yüklü değil. 'pip install transformers torch' komutu ile yükleyin."
    
    try:
        # Donut model ve processor'ı yükle
        processor = DonutProcessor.from_pretrained("naver-clova-ix/donut-base-finetuned-docvqa")
        model = VisionEncoderDecoderModel.from_pretrained("naver-clova-ix/donut-base-finetuned-docvqa")
        
        # GPU varsa kullan
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model.to(device)
        
        # Görüntüyü işle
        pixel_values = processor(image, return_tensors="pt").pixel_values
        pixel_values = pixel_values.to(device)
        
        # Tahmin yap
        with torch.no_grad():
            generated_ids = model.generate(
                pixel_values,
                max_length=512,
                early_stopping=True,
                pad_token_id=processor.tokenizer.pad_token_id,
                eos_token_id=processor.tokenizer.eos_token_id,
                use_cache=True,
                num_beams=1,
                bad_words_ids=[[processor.tokenizer.unk_token_id]],
                return_dict_in_generate=True,
            )
        
        # Sonucu decode et
        generated_text = processor.batch_decode(generated_ids.sequences)[0]
        generated_text = processor.token2json(generated_text)
        
        return f"Donut Analiz Sonucu:\n{generated_text}"
    except Exception as e:
        return f"Donut hatası: {str(e)}"

def layoutparser_extraction(image):
    """LayoutParser ile layout analizi"""
    if not LAYOUTPARSER_AVAILABLE:
        return "LayoutParser kütüphanesi yüklü değil. 'pip install layoutparser' komutu ile yükleyin."
    
    try:
        # PIL Image'i numpy array'e çevir
        img_array = np.array(image)
        
        # LayoutParser ile analiz
        image_analyzer = lp.AutoLayoutModel('lp/PubLayNet/faster_rcnn_R_50_FPN_3x')
        
        # Görüntüyü analiz et
        layout_result = image_analyzer.detect(img_array)
        
        # Sonuçları işle
        result = "LayoutParser Analiz Sonuçları:\n\n"
        
        for i, layout in enumerate(layout_result):
            result += f"Layout {i+1}:\n"
            result += f"  - Tip: {layout.type}\n"
            result += f"  - Confidence: {layout.score:.2f}\n"
            result += f"  - Koordinatlar: {layout.block.coordinates}\n"
            result += f"  - Boyut: {layout.block.width} x {layout.block.height}\n\n"
        
        return result
    except Exception as e:
        return f"LayoutParser hatası: {str(e)}"

def show():
    st.title("OCR Text Extraction & Table Detection")
    st.write("PDF belgelerinden OCR ile metin çıkarma ve tablo tespiti yapın.")
    
    # Kütüphane durumlarını göster
    st.sidebar.header("Kütüphane Durumları")
    st.sidebar.write(f"PaddleOCR: {'✅' if PADDLEOCR_AVAILABLE else '❌'}")
    st.sidebar.write(f"img2table: {'✅' if IMG2TABLE_AVAILABLE else '❌'}")
    st.sidebar.write(f"DeepDoctection: {'✅' if DEEPDOCTECTION_AVAILABLE else '❌'}")
    st.sidebar.write(f"PDFplumber: {'✅' if PDFPLUMBER_AVAILABLE else '❌'}")
    st.sidebar.write(f"Donut: {'✅' if DONUT_AVAILABLE else '❌'}")
    st.sidebar.write(f"LayoutParser: {'✅' if LAYOUTPARSER_AVAILABLE else '❌'}")
    
    col1, col2 = st.columns([1, 1])
    
    if "file_path" in st.session_state and os.path.exists(st.session_state.file_path):
        file_path = st.session_state.file_path
        
        with col1:
            st.subheader("PDF Görüntüleyici")
            pdf_viewer(
                file_path,
                width=820,
                height=1640,
                zoom_level=1,
                viewer_align="center",
                show_page_separator=True,
            )
        
        with col2:
            st.subheader("OCR Teknolojileri")
            
            # Teknoloji seçimi
            ocr_technology = st.selectbox(
                "OCR Teknolojisi Seçin:",
                [
                    "PaddleOCR",
                    "img2table (Tablo Tespiti)",
                    "DeepDoctection",
                    "PDFplumber (Tablo Çıkarma)",
                    "Donut (Belge Analizi)",
                    "LayoutParser (Layout Analizi)"
                ]
            )
            
            # PDF'den görüntü çıkarma seçeneği
            extract_images = st.checkbox("PDF'den görüntüleri çıkar ve OCR uygula", value=False)
            
            if extract_images:
                st.info("PDF'den görüntüler çıkarılıyor...")
                images = extract_images_from_pdf(file_path)
                
                if images:
                    st.success(f"{len(images)} görüntü bulundu")
                    
                    # Görüntü seçimi
                    selected_image_index = st.selectbox(
                        "Analiz edilecek görüntüyü seçin:",
                        options=range(len(images)),
                        format_func=lambda x: f"Sayfa {images[x]['page']} - Görüntü {images[x]['index']+1}"
                    )
                    
                    selected_image = images[selected_image_index]['image']
                    
                    # Seçilen görüntüyü göster
                    st.image(selected_image, caption=f"Seçilen görüntü - Sayfa {images[selected_image_index]['page']}")
                    
                    # OCR işlemi
                    if st.button("OCR Analizi Başlat"):
                        with st.spinner("OCR analizi yapılıyor..."):
                            if ocr_technology == "PaddleOCR":
                                result = paddleocr_extraction(selected_image)
                            elif ocr_technology == "img2table (Tablo Tespiti)":
                                result = img2table_extraction(selected_image)
                            elif ocr_technology == "DeepDoctection":
                                result = deepdoctection_extraction(selected_image)
                            elif ocr_technology == "Donut (Belge Analizi)":
                                result = donut_extraction(selected_image)
                            elif ocr_technology == "LayoutParser (Layout Analizi)":
                                result = layoutparser_extraction(selected_image)
                            else:
                                result = "Geçersiz teknoloji seçimi"
                            
                            st.subheader("OCR Sonucu")
                            st.text_area("Çıkarılan Metin:", result, height=400)
                else:
                    st.warning("PDF'de görüntü bulunamadı")
            
            # PDFplumber için doğrudan dosya analizi
            if ocr_technology == "PDFplumber (Tablo Çıkarma)":
                if st.button("PDFplumber ile Tablo Analizi"):
                    with st.spinner("PDFplumber ile tablo analizi yapılıyor..."):
                        result = pdfplumber_extraction(file_path)
                        st.subheader("PDFplumber Sonucu")
                        st.text_area("Analiz Sonucu:", result, height=400)
            
            # Genel bilgiler
            st.markdown("---")
            st.markdown("### Kullanım Notları:")
            
            if ocr_technology == "PaddleOCR":
                st.info("PaddleOCR: Görüntülerden metin çıkarma için kullanılır. Çok dilli destek sunar.")
            elif ocr_technology == "img2table (Tablo Tespiti)":
                st.info("img2table: Görüntülerden tablo tespiti ve çıkarma için optimize edilmiştir.")
            elif ocr_technology == "DeepDoctection":
                st.info("DeepDoctection: Belge analizi, OCR ve layout tespiti için kapsamlı bir çözüm.")
            elif ocr_technology == "PDFplumber (Tablo Çıkarma)":
                st.info("PDFplumber: PDF'lerden doğrudan tablo çıkarma için kullanılır.")
            elif ocr_technology == "Donut (Belge Analizi)":
                st.info("Donut: Transformer tabanlı belge anlama modeli.")
            elif ocr_technology == "LayoutParser (Layout Analizi)":
                st.info("LayoutParser: Belge layout analizi ve görsel element tespiti.")
            
            # Kurulum talimatları
            st.markdown("### Kurulum Talimatları:")
            st.code("""
# Gerekli kütüphaneleri yükleyin:
pip install paddlepaddle paddleocr
pip install img2table
pip install deepdoctection
pip install pdfplumber
pip install transformers torch
pip install layoutparser
            """)
    
    else:
        st.error("PDF dosyası bulunamadı. Lütfen önce bir PDF yükleyin.")
        st.info("Ana sayfaya gidip PDF yükleyin, sonra bu sayfaya geri dönün.")
