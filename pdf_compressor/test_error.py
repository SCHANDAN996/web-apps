import fitz
import io
import traceback
from PIL import Image

def compress_pdf_to_size(input_bytes, target_kb=245):
    target_bytes = target_kb * 1024
    
    # Intentionally cause an error in native compress or mock it
    
    try:
        doc = fitz.open(stream=input_bytes, filetype="pdf")
        out_pdf = io.BytesIO()
        doc.save(out_pdf, garbage=4, deflate=True)
        doc.close()
        
        if out_pdf.tell() <= target_bytes:
            return out_pdf.getvalue()
    except Exception as e:
        print("Error during native compress:", e)
    
    # If still larger than 250kb, re-render pages as JPEGs
    doc = fitz.open(stream=input_bytes, filetype="pdf")
    num_pages = len(doc)
    
    settings = [(150, 75), (100, 60), (72, 40), (50, 30), (36, 15)]
    
    best_bytes = out_pdf.getvalue()
    
    for dpi, q in settings:
        try:
            new_doc = fitz.open()
            for page_num in range(num_pages):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(dpi=dpi)
                
                # Convert PyMuPDF pixmap to PIL Image
                # FIX: Handle Grayscale
                if pix.n == 1:
                    mode = "L"
                elif pix.n == 2:
                    mode = "LA"
                elif pix.n == 3:
                    mode = "RGB"
                elif pix.n == 4 and pix.alpha:
                    mode = "RGBA"
                elif pix.n == 4 and not pix.alpha:
                    mode = "CMYK"
                else:
                    mode = "RGBA" if pix.alpha else "RGB"
                    
                img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
                if mode in ("RGBA", "LA"):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])
                    img = background
                elif mode != "RGB":
                    img = img.convert("RGB")
                    
                img_io = io.BytesIO()
                img.save(img_io, format="JPEG", quality=q, optimize=True)
                img_bytes = img_io.getvalue()
                
            test_out = io.BytesIO()
            new_doc.save(test_out, garbage=4, deflate=True)
            new_doc.close()
            
            size = test_out.tell()
            best_bytes = test_out.getvalue()
            
            if size <= target_bytes:
                break
        except Exception as e:
            print(f"Error compressing at dpi={dpi}: {e}")
            traceback.print_exc()
            
    doc.close()
    return best_bytes

print("Testing")
