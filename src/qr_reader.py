import cv2
from pyzbar.pyzbar import decode
from src.config import QR_ROI

def read_matricula(image):
    """
    Recorta a área e lê o QR Code contendo a matrícula.
    Retorna a matrícula como string ou None se não encontrar.
    """
    x, y, w, h = QR_ROI
    # Tratamento de erro básico caso as coordenadas passem da imagem
    h_img, w_img = image.shape[:2]
    x = max(0, min(x, w_img))
    y = max(0, min(y, h_img))
    roi = image[y:y+h, x:x+w]
    
    decoded_objects = decode(roi)
    for obj in decoded_objects:
        dados = obj.data.decode("utf-8")
        return dados.strip()
    return None
