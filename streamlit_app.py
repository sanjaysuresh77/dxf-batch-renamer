import os
import re
import io
import zipfile
import streamlit as st
import ezdxf
import tempfile

def extract_series_and_page(filename):
    match = re.search(r'_([A-Z])_(\d{3})', filename)
    if match:
        return f"{match.group(1)}_{match.group(2)}"
    return None

def replace_text_in_dxf(filepath, sht_value, cont_value, title_text):
    filename = os.path.basename(filepath)
    try:
        doc = ezdxf.readfile(filepath)
    except Exception as e:
        st.error(f"Failed to open {filename}: {e}")
        return None

    msp = doc.modelspace()

    def replace_entity_text(entity):
        text = entity.dxf.text.strip()
        if text == 'SHT':
            entity.dxf.text = sht_value
        elif text == 'CONT':
            entity.dxf.text = cont_value
        elif text == 'TITLE1':
            entity.dxf.text = title_text

    for entity in msp:
        if entity.dxftype() in ('TEXT', 'MTEXT'):
            replace_entity_text(entity)
        elif entity.dxftype() == 'INSERT':
            for attrib in entity.attribs:
                if attrib.dxf.tag == 'SHT':
                    attrib.dxf.text = sht_value
                elif attrib.dxf.tag == 'CONT':
                    attrib.dxf.text = cont_value
                elif attrib.dxf.tag == 'TITLE1':
                    attrib.dxf.text = title_text

    for block in doc.blocks:
        for entity in block:
            if entity.dxftype() in ('TEXT', 'MTEXT'):
                replace_entity_text(entity)

    # Save to a temp file and return contents
    temp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".dxf")
    doc.saveas(temp_out.name)
    with open(temp_out.name, "rb") as f:
        filedata = f.read()
    os.unlink(temp_out.name)  # Clean up
    return filename, filedata

def main():
    st.title("SHEET NUMBER")

    uploaded_zip = st.file_uploader("Upload a **ZIP** file containing `.dxf` files.", type="zip")

    if uploaded_zip is not None:
        with zipfile.ZipFile(uploaded_zip, "r") as zip_ref:
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_ref.extractall(tmpdir)
                dxf_files = sorted([
                    f for f in os.listdir(tmpdir) if f.lower().endswith('.dxf')
                ])

                series_page_map = []
                for file in dxf_files:
                    series_page = extract_series_and_page(file)
                    if series_page:
                        series_page_map.append((file, series_page))
                    else:
                        st.warning(f"Skipped invalid file name format: {file}")

                if not series_page_map:
                    st.error("No valid DXF files found in the ZIP.")
                    return

                result_zip_buffer = io.BytesIO()
                with zipfile.ZipFile(result_zip_buffer, "w") as result_zip:
                    for idx, (file, sht_val) in enumerate(series_page_map):
                        cont_val = (
                            series_page_map[idx + 1][1]
                            if idx + 1 < len(series_page_map)
                            else ""
                        )
                        filepath = os.path.join(tmpdir, file)
                        result = replace_text_in_dxf(filepath, sht_val, cont_val, f"TITLE {idx + 1}")
                        if result:
                            filename, filedata = result
                            result_zip.writestr(filename, filedata)
                            st.success(f"Processed: {filename}")

                st.download_button(
                    "Download Processed files",
                    data=result_zip_buffer.getvalue(),
                    file_name="Final_files.zip",
                    mime="application/zip"
                )

if __name__ == "__main__":
    main()
