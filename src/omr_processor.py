import cv2
import numpy as np
from src.config import OMR_CONFIG, ALTERNATIVAS

def evaluate_bubble(image, x, y, w, h, threshold_marcacao):
    """
    Avalia se uma bolha específica está preenchida.
    """
    roi = image[y:y+h, x:x+w]
    
    # Converte pra cinza e aplica gaussian blur suave
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Binarização Invertida (Preto vira branco (255), branco vira preto (0))
    # Para lidar com variações de iluminação, Otsu é bom:
    _, bin_roi = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Contar pixels não-zeros (os que eram escuros no original e agora são brancos)
    total_pixels = w * h
    non_zero = cv2.countNonZero(bin_roi)
    
    ratio = non_zero / float(total_pixels)
    return ratio >= threshold_marcacao, ratio

def get_question_coordinates(q_num, config):
    """
    Calcula as coordenadas da questão e alternativas usando a Questão 1 como âncora 
    e o espaçamento vertical descoberto na Questão 2. 
    Lembrando que na calibração, deve-se selecionar a área abrangendo APENAS a linha de bolhas (A)(B)(C)(D).
    """
    try:
        q1_x, q1_y, w, h = config["questao_1"]
        _, q2_y, _, _ = config["questao_2"]
        esp_y = q2_y - q1_y
        esp_x = w / 4.0 # Assumindo 4 alternativas na largura W
        
        if 1 <= q_num <= 8:
            base_x, base_y = q1_x, q1_y
            offset = q_num - 1
        elif 9 <= q_num <= 16:
            base_x, base_y, _, _ = config["questao_9"]
            offset = q_num - 9
        elif 17 <= q_num <= 24:
            base_x, base_y, _, _ = config["questao_17"]
            offset = q_num - 17
        else:
            raise ValueError(f"Questão {q_num} fora de alcance.")
        
        y_q = base_y + (offset * esp_y)
        # Retorna o (X inicial, Y inicial, tamanho X de 1 bolha, tamanho Y de 1 bolha/linha)
        return int(base_x), int(y_q), int(esp_x), int(h)
    except KeyError as e:
        raise ValueError(f"Configuração ausente para calcular coordenadas: {e}")

def read_answers(image):
    """
    Escaneia as 24 questões baseando-se no layout de blocos OMR_CONFIG.
    """
    respostas = {}
    config = OMR_CONFIG
    thresh = config["threshold_marcacao"]
    
    for q_num in range(1, 25):
        try:
            start_x, start_y, esp_x, esp_y = get_question_coordinates(q_num, config)
        except ValueError:
            continue
        
        # O tamanho da bolha será uns 80% do tamanho da "célula" do grid pra não pegar bordas
        w = int(esp_x * 0.95)
        h = int(esp_y * 0.95)
        offset_x = int(esp_x * 0.025)
        offset_y = int(esp_y * 0.025)
        
        marcadas = []
        for i, alt in enumerate(ALTERNATIVAS):
            bx = start_x + (i * esp_x) + offset_x
            by = start_y + offset_y
            
            # Avalia a bolha
            is_filled, _ = evaluate_bubble(image, int(bx), int(by), w, h, thresh)
            if is_filled:
                marcadas.append(alt)
        
        # Lógica de Classificação
        if len(marcadas) == 0:
            respostas[str(q_num)] = "X"
        elif len(marcadas) == 1:
            respostas[str(q_num)] = marcadas[0]
        else:
            respostas[str(q_num)] = "ANULADA"
            
    return respostas
