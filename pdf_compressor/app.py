import sys
import os
import io
import zipfile
import fitz  # PyMuPDF
from PIL import Image
from flask import Flask, request, send_file, render_template, jsonify
from werkzeug.utils import secure_filename
import traceback

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB max

def compress_pdf_to_size(input_bytes, target_kb=245):
    target_bytes = target_kb * 1024
    
    # Check if PyMuPDF can open it at all
    try:
        doc = fitz.open(stream=input_bytes, filetype="pdf")
    except Exception as e:
        raise Exception(f"Cannot open PDF file format: {e}")
        
    if getattr(doc, 'is_encrypted', False):
        raise Exception("One of your PDFs is encrypted/password protected. Please decrypt it first.")
        
    num_pages = len(doc)
    best_bytes = input_bytes
    
    # First attempt: Native PyMuPDF garbage collection
    try:
        out_pdf = io.BytesIO()
        doc.save(out_pdf, garbage=4, deflate=True)
        if out_pdf.tell() <= target_bytes:
            doc.close()
            return out_pdf.getvalue()
        best_bytes = out_pdf.getvalue()
    except Exception as e:
        print("Error during native compress:", e)
    
    # If still larger, re-render pages as JPEGs
    settings = [(150, 75), (100, 60), (72, 40), (50, 30), (36, 15)]
    
    for dpi, q in settings:
        try:
            new_doc = fitz.open()
            for page_num in range(num_pages):
                page = doc.load_page(page_num)
                # FORCE RGB colorspace to prevent PIL "not enough image data" errors on Grayscale/CMYK
                pix = page.get_pixmap(dpi=dpi, colorspace=fitz.csRGB)
                
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
            traceback.print_exc()
            
    doc.close()
    return best_bytes

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/compress', methods=['POST'])
def compress_files():
    if 'pdfs' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
        
    files = request.files.getlist('pdfs')
    if not files or files[0].filename == '':
        return jsonify({'error': 'No selected files'}), 400
        
    try:
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file in files:
                filename = secure_filename(file.filename)
                if not filename.lower().endswith('.pdf'):
                    continue
                
                input_bytes = file.read()
                compressed_bytes = compress_pdf_to_size(input_bytes, 245)  # 245 KB to be safe
                
                name_part, ext = os.path.splitext(filename)
                new_name = f"{name_part}_compressed{ext}"
                zf.writestr(new_name, compressed_bytes)
        
        memory_file.seek(0)
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name='compressed_pdfs.zip'
        )
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    from threading import Timer
    import webbrowser
    
    def open_browser():
        webbrowser.open_new("http://127.0.0.1:5000")
        
    Timer(1, open_browser).start()
    app.run(port=5000, debug=False)
