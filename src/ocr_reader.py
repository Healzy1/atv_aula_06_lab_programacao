import cv2
import pytesseract
from src.config import HEADER_ROIS, EXTRACTION_MODE

# Configurar o caminho explícito do Tesseract para evitar erros no Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_header_info(image):
    """
    Extrai informações do cabeçalho predefinido.
    Utiliza o Tesseract (Offline) como linha de frente (para nomes impressos/digitados).
    Se o grau de confianca do Tesseract for muito baixo (típico de letra de mão/garrancho),
    aciona o fallback do Gemini apenas se EXTRACTION_MODE for 'auto'.
    """
    extracted_data = {}
    custom_config = r'--oem 3 --psm 7 -l por'
    
    precisa_resgate_ia = False

    for campo, (x, y, w, h) in HEADER_ROIS.items():
        roi = image[y:y+h, x:x+w]
        
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        _, bin_roi = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Faz a leitura capturando os METADADOS para sabermos o nivel de certeza do Tesseract
        dados = pytesseract.image_to_data(bin_roi, config=custom_config, output_type=pytesseract.Output.DICT)
        
        palavras = []
        confiancas = []
        
        for i in range(len(dados['text'])):
            word = dados['text'][i].strip()
            conf = int(dados['conf'][i])
            
            # -1 indica apenas blocos/espaços vazios
            if word and conf > -1:
                palavras.append(word)
                confiancas.append(conf)
                
        texto = " ".join(palavras)
        texto = texto.replace('\n', ' ')
        
        # Sanitização Universal (Limpa hifens, aspas curtas, duplas e curvas do inicio e fim)
        texto = texto.strip(" -'\"”“_")
        
        # Filtros Antidelírio por Campo (Limpeza de ruídos/poeiras lidas pelo Tesseract)
        if campo == "bimestre":
            # Bimestre só deve conter o número do bimestre (1, 2, 3, 4). Corta sujeiras do tipo "ps"
            numeros = "".join(c for c in texto if c.isdigit())
            texto = numeros
        elif campo == "turma":
            # Troca caracter especial mal lido por causa da linha guia, e tira poeira longa
            texto = texto.replace("Ã", "A").replace("ã", "A").replace("~", "")
            if len(texto) > 2: # Turmas normalmente são A, B, 1A
                texto = texto[0] # Pega só a primeira letra se o Tesseract viajau muito
                
        extracted_data[campo] = texto
        
        # HEURÍSTICA DE INTELIGÊNCIA:
        # Tesseract sempre acerta letra de forma (Confianca 80%+).
        # Letra cursiva ("ALL IDO ADO TT") fará a confianca despencar para 30~50.
        media_confianca = sum(confiancas) / len(confiancas) if confiancas else 0
        
        if campo in ["nome"]:
            print(f"      [OCR] Campo {campo} lido como '{texto}' (Confiança: {media_confianca:.2f}%)")
            # Se não conseguiu ler nada ou ficou com muita duvida (< 68%), pede ajuda.
            if len(texto) < 3 or media_confianca < 68:
                precisa_resgate_ia = True
                
    if EXTRACTION_MODE == "auto" and precisa_resgate_ia:
        from src.multimodal_reader import extract_header_with_ai
        print("      [Fallback IA] Tesseract encontrou manuscrito irreconhecível. Direcionando cabeçalho pro Gemini...")
        try:
            dados_ia = extract_header_with_ai(image)
            for key, val in dados_ia.items():
                if val:
                    extracted_data[key] = val
                    
            extracted_data["_usou_ia"] = True
            
        except Exception as e:
            print(f"      [Erro IA] Falha no API do Gemini: {e}. Seguindo com falha de OCR.")

    # Filtros Finais Passa-Tudo (Garante que dados do Tesseract e da IA fiquem perfeitos sempre)
    for campo, texto in extracted_data.items():
        if isinstance(texto, str):
            # Sanitização de aspas residuais e hifens
            texto = texto.strip(" -'\"”“_")
            
            # Anti-alucinações
            if campo == "bimestre":
                texto = "".join(c for c in texto if c.isdigit())
            elif campo == "turma":
                texto = texto.replace("Ã", "A").replace("ã", "A").replace("~", "")
                if len(texto) > 2:
                    texto = texto[0]
                    
            extracted_data[campo] = texto

    return extracted_data
