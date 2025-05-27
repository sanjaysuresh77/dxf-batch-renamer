import os
import streamlit as st
import zipfile
import shutil
import tempfile

def rename_dxf_files(zip_file, find_text, replace_text):
    renamed_files = []
    failed_files = []

    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(tmpdir)

        for filename in os.listdir(tmpdir):
            if filename.lower().endswith(".dxf") and find_text in filename:
                old_path = os.path.join(tmpdir, filename)
                new_filename = filename.replace(find_text, replace_text)
                new_path = os.path.join(tmpdir, new_filename)

                try:
                    os.rename(old_path, new_path)
                    renamed_files.append((filename, new_filename))
                except Exception as e:
                    failed_files.append((filename, str(e)))

        # Move the renamed files into a new temporary directory
        output_dir = tempfile.mkdtemp()
        output_zip_path = os.path.join(output_dir, "renamed_dxf_files.zip")

        with zipfile.ZipFile(output_zip_path, "w") as zf:
            for f in os.listdir(tmpdir):
                if f.endswith(".dxf"):
                    zf.write(os.path.join(tmpdir, f), f)

    return output_zip_path, renamed_files, failed_files

# Streamlit UI
st.title("Batch Rename DXF Files (Streamlit App)")
st.markdown("Upload a `.zip` file containing DXF files.")

uploaded_zip = st.file_uploader("Upload ZIP File", type=["zip"])
find_text = st.text_input("Text to Find in Filename")
replace_text = st.text_input("Replacement Text")

if st.button("Rename Files"):
    if uploaded_zip and find_text:
        with st.spinner("Renaming files..."):
            output_zip_path, renamed_files, failed_files = rename_dxf_files(uploaded_zip, find_text, replace_text)

        st.success(f"Renamed {len(renamed_files)} files.")

        for old, new in renamed_files:
            st.write(f"✅ {old} → {new}")

        if failed_files:
            st.error(f"{len(failed_files)} files failed to rename.")
            for file, err in failed_files:
                st.write(f"❌ {file}: {err}")

        with open(output_zip_path, "rb") as f:
            st.download_button("Download Renamed ZIP", f, file_name="renamed_dxf_files.zip")
    else:
        st.warning("Please upload a ZIP file and enter the text to find.")
