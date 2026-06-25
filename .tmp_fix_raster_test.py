from pathlib import Path

p = Path('full_debug_test.py')
text = p.read_text(encoding='utf-8')
old = '''    vector_raster_pdf = inp / "vector_raster_source.pdf"
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
new = '''    vector_raster_pdf = inp / "vector_raster_source.pdf"
    vec_canvas = canvas.Canvas(str(vector_raster_pdf))
    for page_index in range(3):
        vec_canvas.setFont("Helvetica", 9)
        for row in range(60):
            y = 800 - row * 12
            vec_canvas.drawString(36, y, f"Vector row {page_index+1}-{row+1} | " + ("ABCD1234 " * 12))
            vec_canvas.line(36, y - 2, 560, y - 2)
            if row % 3 == 0:
                vec_canvas.rect(36 + (row % 10) * 18, y - 8, 120, 10, stroke=1, fill=0)
        vec_canvas.showPage()
    vec_canvas.save()
    vector_raster_out = out / "vector_rasterized.pdf"
    vector_pike_out = out / "vector_pike.pdf"
    vector_raster_status = mod.compress_pdf_file(str(vector_raster_pdf), str(vector_raster_out), "标准", "网页式极限压缩")
    vector_pike_status = mod.compress_pdf_file(str(vector_raster_pdf), str(vector_pike_out), "标准", "保留原图")
    vector_raster_img_size = first_pdf_image_size(vector_raster_out)
    record(
        "pdf_compress_web_raster_mode",
        vector_raster_status.startswith("SUCCESS")
        and ":rasterized" in vector_raster_status
        and vector_pike_status.startswith("SUCCESS")
        and vector_raster_out.exists()
        and vector_pike_out.exists()
        and vector_raster_out.stat().st_size < vector_pike_out.stat().st_size
        and vector_raster_img_size[0] > 0
        and vector_raster_img_size[1] > 0,
        {
            "status": vector_raster_status,
            "pike_status": vector_pike_status,
            "source_bytes": vector_raster_pdf.stat().st_size,
            "raster_bytes": vector_raster_out.stat().st_size if vector_raster_out.exists() else 0,
            "pike_bytes": vector_pike_out.stat().st_size if vector_pike_out.exists() else 0,
            "first_image_size": vector_raster_img_size,
        },
    )
'''
text = text.replace(old, new)
p.write_text(text, encoding='utf-8')
print('updated raster test')
