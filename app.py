import streamlit as st
import subprocess
import os
import tempfile
from pathlib import Path
import zipfile
import io

# Path to Ghostscript executable
GHOSTSCRIPT_PATH = "bin/gswin64c.exe"  # Update if needed

def convert_pdf(pdf_path, output_dir, dpi, quality, first_page, last_page, fmt):
    device_map = {
        "JPEG": "jpeg",
        "PNG": "png16m",
        "TIFF": "tiff24nc"
    }
    extension = fmt.lower()
    device = device_map[fmt]
    output_pattern = os.path.join(output_dir, f"page_%03d.{extension}")

    cmd = [
        GHOSTSCRIPT_PATH,
        f"-sDEVICE={device}",
        f"-sOutputFile={output_pattern}",
        f"-r{dpi}",
        "-dNOPAUSE",
        "-dBATCH",
        f"-dFirstPage={first_page}",
        f"-dLastPage={last_page}",
        f"-dJPEGQ={quality}",
        "-dGraphicsAlphaBits=4",
        "-dTextAlphaBits=4",
        "-dNumRenderingThreads=4",
        "-f", pdf_path
    ]

    subprocess.run(cmd, check=True)
    return list(Path(output_dir).glob(f"*.{extension}"))

def create_zip(image_paths):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zipf:
        for img_path in image_paths:
            zipf.write(img_path, arcname=img_path.name)
    zip_buffer.seek(0)
    return zip_buffer

# Streamlit UI
st.set_page_config(page_title="Fast PDF to Image Converter")
st.title("📄 PDF to Image Converter (Fast & High Quality)")

uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")

if uploaded_file:
    st.subheader("Conversion Settings")

    col1, col2 = st.columns(2)
    with col1:
        dpi = st.slider("DPI (Resolution)", 150, 1200, 300, step=50)
        quality = st.slider("JPEG Quality", 1, 100, 95)
    with col2:
        first_page = st.number_input("First Page", min_value=1, value=1)
        last_page = st.number_input("Last Page", min_value=1, value=9999)

    fmt = st.selectbox("Output Format", ["JPEG", "PNG", "TIFF"])

    if st.button("Convert Now"):
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, uploaded_file.name)
            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.read())

            try:
                with st.spinner("Converting pages..."):
                    image_paths = convert_pdf(pdf_path, tmpdir, dpi, quality, first_page, last_page, fmt)

                with st.spinner("Zipping images..."):
                    zip_buffer = create_zip(image_paths)

                st.success("✅ Conversion complete!")
                st.download_button(
                    label="Download ZIP of Images",
                    data=zip_buffer,
                    file_name="converted_images.zip",
                    mime="application/zip"
                )

            except subprocess.CalledProcessError as e:
                st.error("Ghostscript conversion failed.")
                st.exception(e)
