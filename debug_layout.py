import cv2
import os
import sys
from src.pdf_processor import convert_pdf_to_images
from src.config import QR_ROI, HEADER_ROIS, OMR_CONFIG, ALTERNATIVAS

def generate_debug_image(pdf_path):
    print(f"Gerando imagem de debug visual para {pdf_path}...")
    images = convert_pdf_to_images(pdf_path, dpi=300)
    if not images:
        print("Erro: Nenhuma imagem carregada.")
        return
        
    img = images[0] # Pega a primeira pagina
    
    # Desenhar ROI do QR Code em Azul
    x, y, w, h = QR_ROI
    cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 4)
    cv2.putText(img, "QRCODE", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
    
    # Desenhar ROIs do Cabeçalho em Verde
    for campo, (x, y, w, h) in HEADER_ROIS.items():
        cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 3)
        cv2.putText(img, campo, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
    # Desenhar ROIs do OMR em Vermelho
    config = OMR_CONFIG
    
    for q_num in range(1, 25):
        try:
            from src.omr_processor import get_question_coordinates
            start_x, start_y, esp_x, esp_y = get_question_coordinates(q_num, config)
            
            w = int(esp_x * 0.95)
            h = int(esp_y * 0.95)
            offset_x = int(esp_x * 0.025)
            offset_y = int(esp_y * 0.025)
            
            for i, alt in enumerate(ALTERNATIVAS):
                bx = int(start_x + (i * esp_x) + offset_x)
                by = int(start_y + offset_y)
                cv2.rectangle(img, (bx, by), (bx+w, by+h), (0, 0, 255), 2)
                
            # Colocar o número da questão no canto do bloco
            cv2.putText(img, f"Q{q_num}", (start_x - 50, start_y + int(esp_y/2)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        except ValueError:
            pass
            
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "output")
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "debug_layout.jpg")
    cv2.imwrite(out_path, img)
    print(f"Concluído! A imagem foi salva em: {out_path}")
    print("Abra esta imagem para visualizar onde o sistema está 'olhando' cegamente.")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(base_dir, "data", "input")
    arquivos = [f for f in os.listdir(input_dir) if f.lower().endswith(".pdf")]
    
    if arquivos:
        generate_debug_image(os.path.join(input_dir, arquivos[0]))
    else:
        print("Nenhum PDF encontrado em data/input/")
