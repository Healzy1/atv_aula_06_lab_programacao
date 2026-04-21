# src/config.py

# Dicionário de configurações de coordenadas calibradas pela ferramenta
# Assumimos resolução de 300 DPI por padrão na exportação PDF -> Imagem.

QR_ROI = (1923, 439, 412, 368)

HEADER_ROIS = {
    "municipio": (540, 755, 549, 105),
    "escola": (478, 856, 509, 83),
    "ano": (390, 931, 131, 87),
    "turma": (847, 944, 61, 70),
    "bimestre": (1185, 935, 109, 87),
    "nome": (448, 1023, 1932, 65)
}

# Configurações do OMR (Ancorado pelas questões)
OMR_CONFIG = {
    "threshold_marcacao": 0.45,
    "questao_1": (394, 1858, 487, 118), 
    "questao_2": (394, 2019, 487, 122), 
    "questao_9": (1042, 1862, 491, 114), # Ajuste MINIMO final pra esquerda (De 1046 para 1042)
    "questao_17": (1678, 1853, 487, 136) 
}

# Modo de Extração: "offline" (Apenas Tesseract+OpenCV) ou "auto" (Tesseract + Fallback Gemini API)
EXTRACTION_MODE = "auto"

# Opções de alternativas
ALTERNATIVAS = ["A", "B", "C", "D"]
