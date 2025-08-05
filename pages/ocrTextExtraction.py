import os
import streamlit as st
from streamlit_pdf_viewer import pdf_viewer
from paddleocr import PaddleOCR
from pdf2image import convert_from_path
import tempfile
import pandas as pd
from img2table.document import PDF
from img2table.ocr import TesseractOCR


def show():
    st.title("OCR Text Extraction")
    col1, col2 = st.columns([1, 1])

    if "file_path" in st.session_state and os.path.exists(st.session_state.file_path):
        file_path = st.session_state.file_path

        with col1:
            st.subheader("PDF Viewer")
            pdf_viewer(
                file_path,
                width=820,
                height=1640,
                zoom_level=1,
                viewer_align="center",
                show_page_separator=True,
            )

        with col2:
            st.subheader("OCR Extraction Methods")
            ocr_option = st.selectbox(
                "Choose OCR technology:",
                ["PaddleOCR (Advanced)", "PaddleOCR (Simple)", "img2table (Tesseract)"],
            )

            if ocr_option == "PaddleOCR (Advanced)":
                st.info("🚀 PaddleOCR ile metin çıkarımı")

                # Dil seçimi
                language_options = {
                    "Türkçe": "tr",
                    "English": "en",
                    "中文": "ch",
                    "Français": "fr",
                    "Deutsch": "de",
                    "日本語": "japan",
                    "한국어": "korean",
                    "العربية": "ar",
                    "Русский": "ru",
                    "Español": "es",
                    "Português": "pt",
                    "Italiano": "it",
                }
                selected = st.selectbox(
                    "🌍 Dil seçiniz:", list(language_options.keys()), index=0
                )
                lang_code = language_options[selected]

                # OCR başlat
                if st.button("🚀 OCR Başlat"):
                    try:
                        with st.spinner("🔄 PaddleOCR modeli yükleniyor..."):
                            ocr = PaddleOCR(lang=lang_code, use_angle_cls=True)
                        st.success("✅ Model yüklendi!")

                        # Sayfa sayısını al
                        from pypdf import PdfReader

                        reader = PdfReader(file_path)
                        total_pages = len(reader.pages)

                        all_text = ""
                        progress = st.progress(0)

                        # Her sayfayı işle
                        for idx in range(total_pages):
                            # Görüntüye dönüştür
                            images = convert_from_path(
                                file_path,
                                dpi=200,
                                first_page=idx + 1,
                                last_page=idx + 1,
                            )
                            img = images[0]
                            with tempfile.NamedTemporaryFile(
                                suffix=".png", delete=False
                            ) as tmp:
                                img.save(tmp.name)
                                result = ocr.ocr(tmp.name, cls=False)
                            os.unlink(tmp.name)

                            # Metni biriktir
                            for res in result:
                                all_text += res[1][0] + " "
                            all_text += "\n"

                            progress.progress((idx + 1) / total_pages)

                        # Sonuçları göster
                        st.subheader("📝 Çıkarılan Metin")
                        st.text_area("Metin:", all_text, height=400)

                    except Exception as e:
                        st.error(f"❌ OCR hatası: {e}")
            elif ocr_option == "PaddleOCR (Simple)":
                st.info("🚀 PaddleOCR ile basit metin çıkarımı")

                # Dil seçimi - doğru dil kodları
                language_options = {
                    "Türkçe": "tr",
                    "English": "en",
                    "中文": "ch",
                    "Français": "fr",
                    "Deutsch": "de",
                    "日本語": "japan",
                    "한국어": "korean",
                    "العربية": "ar",
                    "Русский": "ru",
                    "Español": "es",
                    "Português": "pt",
                    "Italiano": "it",
                }

                selected_lang = st.selectbox(
                    "🌍 Dil seçiniz:", list(language_options.keys()), index=0
                )
                lang_code = language_options[selected_lang]

                # OCR işlemi başlat
                if st.button("🚀 OCR İşlemini Başlat", type="primary"):
                    try:
                        # PaddleOCR'ı başlat
                        with st.spinner("🔄 PaddleOCR modeli yükleniyor..."):
                            ocr = PaddleOCR(use_angle_cls=True, lang=lang_code)

                        st.success("✅ PaddleOCR başarıyla yüklendi!")

                        # PDF'i görüntülere dönüştür
                        with st.spinner("🖼️ PDF sayfaları görüntüye dönüştürülüyor..."):
                            images = convert_from_path(file_path, dpi=200)

                        # OCR işlemi
                        all_text = ""
                        progress_bar = st.progress(0)
                        status_text = st.empty()

                        for idx, img in enumerate(images):
                            current_page = idx + 1
                            status_text.text(f"⏳ Sayfa {current_page} işleniyor...")
                            progress_bar.progress((idx + 1) / len(images))

                            # Geçici dosya oluştur
                            with tempfile.NamedTemporaryFile(
                                suffix=".png", delete=False
                            ) as tmp_img:
                                img.save(tmp_img.name)

                                # OCR uygula - cls parametresini kaldırdık
                                result = ocr.ocr(tmp_img.name)

                                if result and result[0]:  # Sonuç kontrolü
                                    page_text = ""
                                    for line in result[0]:
                                        if line:  # Boş satır kontrolü
                                            text = line[1][0]  # Sadece metni al
                                            page_text += text + " "

                                    all_text += f"\n--- Sayfa {current_page} ---\n{page_text.strip()}\n"

                                # Geçici dosyayı sil
                                os.unlink(tmp_img.name)

                        status_text.text("✅ OCR işlemi tamamlandı!")
                        progress_bar.progress(1.0)

                        # Sonuçları göster
                        st.subheader("📝 Çıkarılan Metin")
                        st.text_area("Çıkarılan Metin:", all_text, height=400)

                        # Metin indirme
                        st.download_button(
                            label="💾 Metni TXT dosyası olarak indir",
                            data=all_text,
                            file_name="extracted_text.txt",
                            mime="text/plain",
                        )

                        if all_text.strip():
                            st.success("🎉 Metin başarıyla çıkarıldı!")
                        else:
                            st.warning("⚠️ Hiç metin bulunamadı.")

                    except Exception as e:
                        st.error(f"❌ PaddleOCR hatası: {str(e)}")
                        st.info(
                            """
                        **Olası çözümler:**
                        - İnternet bağlantınızı kontrol edin (ilk kullanımda model indirilir)
                        - Farklı bir dil seçmeyi deneyin
                        - PDF dosyasının bozuk olmadığından emin olun
                        - Uygulamayı yeniden başlatın
                        """
                        )

                        # Hata detayları (debug için)
                        with st.expander("🔧 Hata Detayları (Geliştiriciler için)"):
                            st.code(str(e))

            elif ocr_option == "img2table (Tesseract)":
                st.info("🔧 img2table ile OCR'dan tablo ve/veya metin çıkarımı")
                tesseract_lang = st.text_input(
                    "Tesseract language(s) (örn: eng+tur)", value="eng+tur"
                )
                extraction_mode = st.radio(
                    "Çıkarım türü seçiniz:", ["Sadece Metin", "Sadece Tablo", "Hepsi"]
                )

                if st.button("🚀 Tesseract OCR Başlat", type="primary"):
                    with st.spinner("PDF işleniyor ve OCR uygulanıyor..."):
                        try:
                            pdf_doc = PDF(file_path)
                            ocr_engine = TesseractOCR(lang=tesseract_lang)
                            extracted_tables = pdf_doc.extract_tables(ocr=ocr_engine)

                            # img2table toplu metin çıkarımı API'si yoksa, sayfa sayfa döngüyle çıkar
                            extracted_text = ""
                            if hasattr(pdf_doc, "pages"):
                                for page in pdf_doc.pages:
                                    if hasattr(page, "text") and page.text:
                                        extracted_text += f"\n--- Page {page.number} ---\n{page.text.strip()}\n"
                            else:
                                extracted_text = None

                            if extraction_mode == "Sadece Metin":
                                if extracted_text:
                                    st.success("OCR ile çıkarılan metin:")
                                    st.text_area("Metin", extracted_text, height=400)
                                else:
                                    st.warning(
                                        "Metin bulunamadı veya OCR başarısız oldu."
                                    )

                            elif extraction_mode == "Sadece Tablo":
                                if extracted_tables:
                                    st.success(
                                        f"{len(extracted_tables)} tablo bulundu."
                                    )
                                    for i, tbl in enumerate(extracted_tables):
                                        st.write(f"**Tablo {i+1}:**")
                                        if hasattr(tbl, "df"):
                                            df = pd.DataFrame(tbl.df)
                                            st.dataframe(df)
                                        else:
                                            st.info(
                                                f"Tablo verisi uygun formatta değil: {tbl}"
                                            )
                                else:
                                    st.warning(
                                        "Tablo bulunamadı veya OCR başarısız oldu."
                                    )

                            else:  # Hepsi
                                if extracted_text:
                                    st.success("OCR ile çıkarılan metin:")
                                    st.text_area("Metin", extracted_text, height=200)
                                else:
                                    st.warning(
                                        "Metin bulunamadı veya OCR başarısız oldu."
                                    )

                                if extracted_tables:
                                    st.success(
                                        f"{len(extracted_tables)} tablo bulundu."
                                    )
                                    for i, tbl in enumerate(extracted_tables):
                                        st.write(f"**Tablo {i+1}:**")
                                        if hasattr(tbl, "df"):
                                            df = pd.DataFrame(tbl.df)
                                            st.dataframe(df)
                                        else:
                                            st.info(
                                                f"Tablo verisi uygun formatta değil: {tbl}"
                                            )
                                else:
                                    st.warning(
                                        "Tablo bulunamadı veya OCR başarısız oldu."
                                    )

                        except Exception as e:
                            st.error(f"Tesseract OCR hatası: {str(e)}")

    else:
        st.error("PDF file not found. Please upload again.")
