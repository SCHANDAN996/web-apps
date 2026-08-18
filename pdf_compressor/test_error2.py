import sys
import os
import io
import zipfile
import fitz
from PIL import Image
from werkzeug.utils import secure_filename
import traceback

def compress_pdf_to_size(input_bytes, target_kb=245):
    target_bytes = target_kb * 1024
    
    # First attempt: Native PyMuPDF garbage collection
    try:
        doc = fitz.open(stream=input_bytes, filetype="pdf")
        out_pdf = io.BytesIO()
        doc.save(out_pdf, garbage=4, deflate=True)
        doc.close()
        
        if out_pdf.tell() <= target_bytes:
            return out_pdf.getvalue()
    except Exception as e:
        print("Error during native compress:", e)
        out_pdf = None
    
    # If still larger than 250kb, re-render pages as JPEGs
    doc = fitz.open(stream=input_bytes, filetype="pdf")
    num_pages = len(doc)
    
    settings = [(150, 75), (100, 60), (72, 40), (50, 30), (36, 15)]
    
    best_bytes = out_pdf.getvalue() if out_pdf else input_bytes
    
    for dpi, q in settings:
        try:
            new_doc = fitz.open()
            for page_num in range(num_pages):
                page = doc.load_page(page_num)
                # Create grayscale explicitly
                pix = page.get_pixmap(dpi=dpi, colorspace=fitz.csGRAY)
                
                # Convert PyMuPDF pixmap to PIL Image
                mode = "RGBA" if pix.alpha else "RGB"
                img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
                if mode == "RGBA":
                    # Convert transparent background to white
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])
                    img = background
                
                img_io = io.BytesIO()
                img.save(img_io, format="JPEG", quality=q, optimize=True)
                img_bytes = img_io.getvalue()
                
                img_doc = fitz.open(stream=img_bytes, filetype="jpeg")
                pdf_bytes_tmp = img_doc.convert_to_pdf()
                img_doc.close()
                
                page_doc = fitz.open(stream=pdf_bytes_tmp, filetype="pdf")
                new_doc.insert_pdf(page_doc)
                page_doc.close()
                
            test_out = io.BytesIO()
            new_doc.save(test_out, garbage=4, deflate=True)
            new_doc.close()
            
            size = test_out.tell()
            best_bytes = test_out.getvalue()
            
            if size <= target_bytes:
                break
        except Exception as e:
            print(f"Error compressing at dpi={dpi}: {e}")
            raise e
            
    doc.close()
    return best_bytes

try:
    with open("test_large.pdf", "rb") as f:
        data = f.read()
    res = compress_pdf_to_size(data, 2)
    print("Success")
except Exception as e:
    import traceback
    traceback.print_exc()

