import fitz
import io
from PIL import Image

def compress_pdf(input_path, output_path, target_kb=250):
    target_bytes = target_kb * 1024
    
    doc = fitz.open(input_path)
    # First try native compress
    doc.save(output_path, garbage=4, deflate=True)
    
    import os
    if os.path.getsize(output_path) <= target_bytes:
        print("Native compression worked.")
        return
        
    num_pages = len(doc)
    print(f"Num pages: {num_pages}")
    
    # Settings to try (DPI, JPEG Quality)
    settings = [(150, 75), (100, 60), (72, 50), (50, 30), (36, 20)]
    
    for dpi, q in settings:
        new_doc = fitz.open()
        for page_num in range(num_pages):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=dpi)
            
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img_io = io.BytesIO()
            img.save(img_io, format="JPEG", quality=q, optimize=True)
            img_bytes = img_io.getvalue()
            
            img_doc = fitz.open(stream=img_bytes, filetype="jpeg")
            pdfbytes = img_doc.convert_to_pdf()
            img_doc.close()
            
            page_doc = fitz.open(stream=pdfbytes, filetype="pdf")
            new_doc.insert_pdf(page_doc)
            page_doc.close()
            
        new_doc.save(output_path, garbage=4, deflate=True)
        new_doc.close()
        
        size = os.path.getsize(output_path)
        print(f"Tried DPI={dpi}, Quality={q} -> Size: {size/1024:.2f} KB")
        if size <= target_bytes:
            print("Successfully compressed.")
            return

    print("Compressed as much as possible.")

files = []
with open("test.txt", "w") as f:
    for i in range(100):
        f.write("Hello World this is a lot of text to make a page large " * 100 + "\n")

import fitz as fz
tdoc = fz.open()
tp = tdoc.new_page()
tp.insert_text((50, 50), "Hello big " * 500)
tdoc.save("test_large.pdf")
compress_pdf("test_large.pdf", "test_compressed.pdf")
