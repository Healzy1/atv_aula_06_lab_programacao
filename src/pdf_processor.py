import fitz  # PyMuPDF
import cv2
import numpy as np

def convert_pdf_to_images(pdf_path, dpi=300):
    """
    Converte um PDF de múltiplas páginas em uma lista de imagens no formato OpenCV (numpy array).
    """
    doc = fitz.open(pdf_path)
    images = []
    
    # Fator de zoom para atingir ~300 DPI (72 DPI é o padrão, 300/72 ≈ 4.16)
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    
    for page_idx in range(len(doc)):
        page = doc.load_page(page_idx)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        
        # Converter os bytes do pixmap para um array numpy (RGB)
        img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        
        # O PyMuPDF gera RGB, OpenCV usa BGR.
        if pix.n == 3:
            img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        else:
            img_cv = img_array
            
        images.append(img_cv)
        
    return images
