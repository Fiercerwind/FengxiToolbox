from pathlib import Path

p = Path('full_debug_test.py')
text = p.read_text(encoding='utf-8')

text = text.replace(
    '        and "极限小体积" in PDF_IMAGE_COMPRESS_LEVELS_MODULE\n',
    '        and "极限小体积" in PDF_IMAGE_COMPRESS_LEVELS_MODULE\n        and "网页式极限压缩" in PDF_IMAGE_COMPRESS_LEVELS_MODULE\n'
)

needle = '''    record(
        "pdf_compress_long_scan_keeps_readable_width",
        standard_status.startswith("SUCCESS")
        and long_standard.exists()
        and standard_image_size[0] >= 1080
        and standard_image_size[1] >= 6000
        and tiny_status.startswith("SUCCESS")
        and tiny_image_size[0] < standard_image_size[0],
        {
            "standard_status": standard_status,
            "tiny_status": tiny_status,
            "standard_size": standard_image_size,
            "tiny_size": tiny_image_size,
            "standard_bytes": long_standard.stat().st_size if long_standard.exists() else 0,
            "tiny_bytes": long_tiny.stat().st_size if long_tiny.exists() else 0,
        },
    )
'''
insert = needle + '''
    vector_raster_pdf = inp / "vector_raster_source.pdf"
    make_pdf(vector_raster_pdf, ["vector page one", "vector page two", "vector page three"] * 20)
    vector_raster_out = out / "vector_rasterized.pdf"
    vector_raster_status = mod.compress_pdf_file(str(vector_raster_pdf), str(vector_raster_out), "标准", "网页式极限压缩")
    vector_raster_img_size = first_pdf_image_size(vector_raster_out)
    record(
        "pdf_compress_web_raster_mode",
        vector_raster_status.startswith("SUCCESS")
        and ":rasterized" in vector_raster_status
        and vector_raster_out.exists()
        and vector_raster_out.stat().st_size < vector_raster_pdf.stat().st_size
        and vector_raster_img_size[0] > 0
        and vector_raster_img_size[1] > 0,
        {
            "status": vector_raster_status,
            "source_bytes": vector_raster_pdf.stat().st_size,
            "output_bytes": vector_raster_out.stat().st_size if vector_raster_out.exists() else 0,
            "first_image_size": vector_raster_img_size,
        },
    )
'''
text = text.replace(needle, insert)

p.write_text(text, encoding='utf-8')
print('patched tests')
