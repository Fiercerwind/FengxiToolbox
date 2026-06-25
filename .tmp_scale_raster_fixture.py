from pathlib import Path

p = Path('full_debug_test.py')
text = p.read_text(encoding='utf-8')
old = '    vec_canvas = canvas.Canvas(str(vector_raster_pdf))\n    for page_index in range(3):\n        vec_canvas.setFont("Helvetica", 9)\n        for row in range(60):\n            y = 800 - row * 12\n            vec_canvas.drawString(36, y, f"Vector row {page_index+1}-{row+1} | " + ("ABCD1234 " * 12))\n            vec_canvas.line(36, y - 2, 560, y - 2)\n            if row % 3 == 0:\n                vec_canvas.rect(36 + (row % 10) * 18, y - 8, 120, 10, stroke=1, fill=0)\n        vec_canvas.showPage()\n    vec_canvas.save()\n'
new = '    vec_canvas = canvas.Canvas(str(vector_raster_pdf))\n    for page_index in range(12):\n        vec_canvas.setFont("Helvetica", 8)\n        for row in range(85):\n            y = 812 - row * 9\n            vec_canvas.drawString(22, y, f"Vector row {page_index+1:02d}-{row+1:02d} | " + ("ABCD1234 xyz " * 22))\n            vec_canvas.line(20, y - 1, 585, y - 1)\n            vec_canvas.line(20, y + 2, 585, y + 2)\n            vec_canvas.rect(20 + (row % 15) * 12, y - 7, 160, 8, stroke=1, fill=0)\n            vec_canvas.circle(520 - (row % 8) * 14, y - 3, 4, stroke=1, fill=0)\n        vec_canvas.showPage()\n    vec_canvas.save()\n'
text = text.replace(old, new)
p.write_text(text, encoding='utf-8')
print('scaled raster fixture')
