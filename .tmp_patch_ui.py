from pathlib import Path

p = Path('Fengxi_Toolbox.py')
text = p.read_text(encoding='utf-8')
text = text.replace(
    'PDF 压缩程度控制对象清理、字体和数据流压缩；图片压缩程度控制内嵌图片的重压缩和降采样。',
    'PDF 压缩程度控制对象清理、字体和数据流压缩；图片压缩程度控制内嵌图片的重压缩和降采样。网页式极限压缩会把整页转成图片以换取更小体积。'
)
text = text.replace(
    '提示：如果 PDF 主要由扫描图片组成，调高图片压缩更有效；如果 PDF 主要是文字，PDF 压缩程度通常更关键。',
    '提示：如果 PDF 主要由扫描图片组成，调高图片压缩更有效；如果 PDF 主要是文字，PDF 压缩程度通常更关键。若选择“网页式极限压缩”，页面会转成图片，适合上传分享，不适合复制、搜索或编辑文本。'
)
text = text.replace(
    '        elif engine == "pymupdf":\n            suffix = " | 引擎 内置"\n',
    '        elif engine == "pymupdf":\n            suffix = " | 引擎 内置"\n        elif engine == "rasterized":\n            suffix = " | 引擎 网页式栅格化"\n'
)
p.write_text(text, encoding='utf-8')
print('patched ui')
