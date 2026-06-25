from pathlib import Path
repls = [
    ('网页式极限压缩', '图片化压缩'),
    ('网页式栅格化', '图片化'),
    ('网页式压缩', '图片化压缩'),
]
for rel in ['tools/fx_pdf_compress_core.py','Fengxi_Toolbox.py','full_debug_test.py','memory/categories/pdf-file-meta-zip.md','memory/debug-status.md']:
    p = Path(rel)
    text = p.read_text(encoding='utf-8')
    for a,b in repls:
        text = text.replace(a,b)
    p.write_text(text, encoding='utf-8')
print('renamed')
