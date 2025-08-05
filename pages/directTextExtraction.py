import os
import streamlit as st
from streamlit_pdf_viewer import pdf_viewer
import pymupdf4llm
import pdfplumber
import fitz
import pandas as pd
import camelot
from unstructured.partition.pdf import partition_pdf


def show():
    st.title("Direct Text Extraction")
    st.write("Here you will see the results after processing your PDF.")

    col1, col2 = st.columns([1, 1])

    if "file_path" in st.session_state and os.path.exists(st.session_state.file_path):
        file_path = st.session_state.file_path

        with col1:
            pdf_viewer(
                file_path,
                width=820,
                height=1640,
                zoom_level=1,
                viewer_align="center",
                show_page_separator=True,
            )
        with col2:
            option = st.selectbox(
                "Choose PDF processing method:",
                [
                    "PyMuPDF (fitz)",
                    "PDFplumber",
                    "Camelot (Tables Only)",
                    "Unstructured (Fast Strategy)",
                    "Unstructured (Fast Strategy)",
                    "Unstructured (Table Extraction)",
                ],
            )

            if option == "PyMuPDF (fitz)":
                st.subheader("PyMuPDF (fitz) Text & Table Extraction")

                pymupdf_option = st.radio(
                    "Select extraction mode:",
                    [
                        "All Text",
                        "Specific Page",
                        "Markdown/JSON Output",
                        "Search Text",
                        "Table Detection",
                        "Image Extraction",
                    ],
                )

                doc = fitz.open(file_path)

                if pymupdf_option == "All Text":
                    all_text = ""
                    for page_num in range(doc.page_count):
                        page = doc[page_num]
                        all_text += (
                            f"\n--- Page {page_num + 1} ---\n{page.get_text()}\n"
                        )
                    st.text_area("Full Document Text:", all_text, height=400)

                elif pymupdf_option == "Specific Page":
                    page_number = st.number_input(
                        "Enter page number:",
                        min_value=1,
                        max_value=doc.page_count,
                        step=1,
                        value=1,
                    )
                    page = doc[page_number - 1]
                    page_text = page.get_text()
                    st.text_area(f"Page {page_number} Text:", page_text, height=400)

                elif pymupdf_option == "Markdown/JSON Output":
                    output_format = st.selectbox("Output Format:", ["Markdown", "JSON"])
                    if output_format == "Markdown":
                        for page_num in range(doc.page_count):
                            md_text = pymupdf4llm.to_markdown(
                                file_path, pages=[page_num]
                            )
                            st.markdown("---")
                            st.markdown(f"### Page {page_num + 1}\n{md_text}")
                    elif output_format == "JSON":
                        for page_num in range(doc.page_count):
                            page = doc[page_num]
                            json_text = page.get_text("dict")
                            st.json({f"Page {page_num + 1}": json_text})

                elif pymupdf_option == "Search Text":
                    search_term = st.text_input("Enter text to search:")
                    if search_term:
                        results = []
                        for page_num in range(doc.page_count):
                            page = doc[page_num]
                            text_instances = page.search_for(search_term)
                            if text_instances:
                                results.append(
                                    {
                                        "page": page_num + 1,
                                        "occurrences": len(text_instances),
                                        "coordinates": text_instances,
                                    }
                                )

                        if results:
                            st.success(
                                f"Found '{search_term}' in {len(results)} page(s)"
                            )
                            for result in results:
                                st.write(
                                    f"**Page {result['page']}:** {result['occurrences']} occurrence(s)"
                                )
                                for i, rect in enumerate(result["coordinates"]):
                                    st.write(
                                        f"  Position {i+1}: ({rect.x0:.1f}, {rect.y0:.1f}) to ({rect.x1:.1f}, {rect.y1:.1f})"
                                    )
                        else:
                            st.warning(f"Text '{search_term}' not found in document")

                elif pymupdf_option == "Table Detection":
                    found_any_table = False
                    for page_num in range(doc.page_count):
                        page = doc[page_num]
                        table_finder = page.find_tables()
                        tables = table_finder.tables if table_finder else []
                        if tables:
                            found_any_table = True
                            st.success(
                                f"Found {len(tables)} table(s) on page {page_num + 1}"
                            )
                            for i, table in enumerate(tables):
                                st.write(f"**Page {page_num + 1} - Table {i + 1}:**")
                                table_data = table.extract()
                                if table_data:
                                    if table_data[0]:
                                        columns = []
                                        for j, col in enumerate(table_data[0]):
                                            if col is None or col == "":
                                                columns.append(f"Column_{j+1}")
                                            else:
                                                columns.append(str(col))

                                        seen = {}
                                        unique_columns = []
                                        for col in columns:
                                            if col in seen:
                                                seen[col] += 1
                                                unique_columns.append(
                                                    f"{col}_{seen[col]}"
                                                )
                                            else:
                                                seen[col] = 0
                                                unique_columns.append(col)

                                        df = pd.DataFrame(
                                            table_data[1:], columns=unique_columns
                                        )
                                    else:
                                        num_cols = (
                                            len(table_data[1])
                                            if len(table_data) > 1
                                            else 1
                                        )
                                        columns = [
                                            f"Column_{j+1}" for j in range(num_cols)
                                        ]
                                        df = pd.DataFrame(
                                            table_data[1:], columns=columns
                                        )

                                    st.dataframe(df)
                        else:
                            st.warning(f"No tables found on page {page_num + 1}")
                    if not found_any_table:
                        st.warning("No tables found in the document.")

                elif pymupdf_option == "Image Extraction":
                    for page_num in range(doc.page_count):
                        page = doc[page_num]
                        image_list = page.get_images()
                        if image_list:
                            st.success(
                                f"Page {page_num + 1}: {len(image_list)} embedded image(s) found"
                            )
                            for i, img in enumerate(image_list):
                                xref = img[0]
                                base_image = doc.extract_image(xref)
                                image_bytes = base_image["image"]
                                image_ext = base_image["ext"]
                                st.image(
                                    image_bytes,
                                    caption=f"Page {page_num + 1} - Image {i+1} (.{image_ext})",
                                )

                doc.close()

            elif option == "PDFplumber":
                st.subheader("PDFplumber Text & Table Extraction")

                plumber_option = st.radio(
                    "Select extraction mode:",
                    [
                        "All Text",
                        "Specific Page",
                        "Table Extraction",
                        "Image Extraction",
                    ],
                )

                with pdfplumber.open(file_path) as pdf:

                    if plumber_option == "All Text":
                        all_text = ""
                        for page_num, page in enumerate(pdf.pages):
                            page_text = page.extract_text()
                            if page_text:
                                all_text += (
                                    f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                                )
                        st.text_area("Full Document Text:", all_text, height=400)

                    elif plumber_option == "Specific Page":
                        page_number = st.number_input(
                            "Enter page number:",
                            min_value=1,
                            max_value=len(pdf.pages),
                            step=1,
                            value=1,
                        )
                        page = pdf.pages[page_number - 1]
                        page_text = page.extract_text()
                        st.text_area(
                            f"Page {page_number} Text:",
                            page_text or "No text found",
                            height=400,
                        )

                    elif plumber_option == "Table Extraction":
                        found_tables = False
                        for page_num, page in enumerate(pdf.pages):
                            tables = page.extract_tables()
                            if tables:
                                found_tables = True
                                st.success(
                                    f"Page {page_num + 1}: {len(tables)} table(s) found"
                                )
                                for i, table in enumerate(tables):
                                    if table and len(table) > 0:
                                        st.write(
                                            f"**Page {page_num + 1} - Table {i + 1}:**"
                                        )
                                        if table[0]:
                                            columns = []
                                            for j, col in enumerate(table[0]):
                                                if col is None or col == "":
                                                    columns.append(f"Column_{j+1}")
                                                else:
                                                    columns.append(str(col))

                                            seen = {}
                                            unique_columns = []
                                            for col in columns:
                                                if col in seen:
                                                    seen[col] += 1
                                                    unique_columns.append(
                                                        f"{col}_{seen[col]}"
                                                    )
                                                else:
                                                    seen[col] = 0
                                                    unique_columns.append(col)

                                            df = pd.DataFrame(
                                                table[1:], columns=unique_columns
                                            )
                                        else:
                                            num_cols = (
                                                len(table[1]) if len(table) > 1 else 1
                                            )
                                            columns = [
                                                f"Column_{j+1}" for j in range(num_cols)
                                            ]
                                            df = pd.DataFrame(
                                                table[1:], columns=columns
                                            )

                                        st.dataframe(df)

                        if not found_tables:
                            st.warning("No tables found in the document")

                    elif plumber_option == "Image Extraction":
                        found_images = False
                        for page_num, page in enumerate(pdf.pages):
                            if hasattr(page, "images") and page.images:
                                found_images = True
                                st.success(
                                    f"Page {page_num + 1}: {len(page.images)} image(s) found"
                                )
                                for i, img in enumerate(page.images):
                                    st.write(f"**Image {i + 1}:**")
                                    st.write(
                                        f"Position: ({img['x0']:.1f}, {img['y0']:.1f}) to ({img['x1']:.1f}, {img['y1']:.1f})"
                                    )
                                    size_width = img["x1"] - img["x0"]
                                    size_height = img["y1"] - img["y0"]
                                    st.write(f"Size: {size_width} x {size_height}")

                                    page_height = page.height
                                    corrected_y0 = page_height - img["y1"]
                                    corrected_y1 = page_height - img["y0"]

                                    bbox = (
                                        img["x0"],
                                        corrected_y0,
                                        img["x1"],
                                        corrected_y1,
                                    )
                                    cropped_page = page.crop(bbox)

                                    try:
                                        cropped_image = cropped_page.to_image(
                                            resolution=150
                                        )
                                        st.image(
                                            cropped_image.original,
                                            caption=f"Page {page_num + 1} - Image {i + 1} (Cropped)",
                                        )
                                    except Exception as e:
                                        st.warning(
                                            f"Could not display cropped image: {str(e)}"
                                        )
                                        st.write(
                                            f"Debug info - Page height: {page_height}, Original bbox: ({img['x0']}, {img['y0']}, {img['x1']}, {img['y1']})"
                                        )
                                        st.write(f"Corrected bbox: {bbox}")

                                    if "object" in img:
                                        st.write(f"Object ID: {img['object']}")
                                    st.write("---")

            elif option == "Camelot (Tables Only)":
                st.subheader("Camelot Table Extraction")
                camelot_option = st.radio("Select Camelot mode:", ["Stream", "Lattice"])
                pages_param = "all"

                try:
                    tables = camelot.read_pdf(
                        file_path, flavor=camelot_option.lower(), pages=pages_param
                    )

                    if len(tables) > 0:
                        st.success(f"Found {len(tables)} table(s)")

                        for i, table in enumerate(tables):
                            st.write(f"**Table {i + 1} (Page {table.page}):**")

                            accuracy = table.parsing_report["accuracy"]
                            whitespace = table.parsing_report["whitespace"]
                            st.write(
                                f"Accuracy: {accuracy:.2f}%, Whitespace: {whitespace:.2f}%"
                            )

                            df = table.df
                            st.dataframe(df)

                            st.write("---")
                    else:
                        st.warning("No tables found in the document")

                except Exception as e:
                    st.error(f"Error extracting tables: {str(e)}")
                    st.info(
                        "Note: Camelot only works with text-based PDFs, not scanned images"
                    )

            elif option == "Unstructured (Fast Strategy)":
                st.subheader("Unstructured Fast Strategy")

                include_page_breaks = st.checkbox("Include page breaks", value=True)

                try:
                    elements = partition_pdf(
                        filename=file_path,
                        strategy="fast",
                        include_page_breaks=include_page_breaks,
                    )

                    text_elements = [
                        elem
                        for elem in elements
                        if elem.category
                        in [
                            "NarrativeText",
                            "Title",
                            "ListItem",
                            "UncategorizedText",
                        ]
                    ]

                    if text_elements:
                        st.success(f"Found {len(text_elements)} text element(s)")
                        all_text = ""
                        for i, elem in enumerate(text_elements):
                            all_text += f"{elem.text}\n\n"
                        st.text_area("Extracted Text:", all_text, height=400)
                    else:
                        st.warning("No text elements found")

                except Exception as e:
                    st.error(f"Error processing with Unstructured: {str(e)}")
                    st.info(
                        "Make sure the 'unstructured' library is properly installed"
                    )

    else:
        st.error("PDF file not found. Please upload again.")
