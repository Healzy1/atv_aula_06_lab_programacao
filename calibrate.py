import cv2
import sys
from src.pdf_processor import convert_pdf_to_images

def calibrate(pdf_path):
    print(f"Convertendo '{pdf_path}' para imagem. Aguarde...")
    images = convert_pdf_to_images(pdf_path, dpi=300)
    
    if not images:
        print("Erro: PDF não gerou nenhuma imagem.")
        return
        
    img = images[0]
    # Redimensiona para caber na tela sem cortar a parte de baixo
    h, w = img.shape[:2]
    
    # Calcula a escala dinamicamente para que a altura maxima seja 800 pixels
    scale_percent = 800.0 / h * 100.0 
    width = int(w * scale_percent / 100)
    height = int(h * scale_percent / 100)
    dim = (width, height)
    
    resized = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)

    print("==================================================")
    print("--- MODO DE CALIBRAÇÃO SEQUENCIAL ---")
    print("Vamos passar pelos campos um a um para facilitar!")
    print("Arraste com o mouse esquerdo sobre a região pedida.")
    print("Aperte ENTER para confirmar o quadrado e ir para a próxima bateria.")
    print("==================================================\n")
    
    items_to_calibrate = [
        "1. QR_ROI (A area total em volta do QR Code)",
        "2. municipio (O campo com municipio)",
        "3. escola (O campo com nome da escola)",
        "4. ano",
        "5. turma",
        "6. bimestre",
        "7. nome (O campo onde aluno escreve o nome)",
        "8. questao_1 (Selecione APENAS AS 4 BOLHAS A B C D da questao 1. Nao pegue o texto Q1!)",
        "9. questao_2 (Selecione APENAS AS 4 BOLHAS da questao 2. P/ Distancia Y)",
        "10. questao_9 (1a da Segunda Coluna - APENAS AS BOLHAS)",
        "11. questao_17 (1a da Terceira Coluna - APENAS AS BOLHAS)"
    ]

    resultados = {}

    for item in items_to_calibrate:
        print(f"-> Selecione no grafico agora: {item}")
        r = cv2.selectROI(item, resized, fromCenter=False, showCrosshair=True)
        cv2.destroyAllWindows()
        
        # Multiplicar de volta para a resolução do PDF original (300dpi)
        x_real = int(r[0] / (scale_percent / 100))
        y_real = int(r[1] / (scale_percent / 100))
        w_real = int(r[2] / (scale_percent / 100))
        h_real = int(r[3] / (scale_percent / 100))
        
        resultados[item] = (x_real, y_real, w_real, h_real)
        
    print("\n\n=============== PRONTO! ACABOU! ===============")
    print("Copie os dados abaixo e cole / substitua dentro do seu src/config.py :\n")
    
    for key, val in resultados.items():
        chave_limpa = key.split(" ")[1]
        
        if "QR_ROI" in chave_limpa:
            print(f"QR_ROI = {val}")
        else:
            print(f'"{chave_limpa}": {val},')
            
    print("==================================================")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python calibrate.py <caminho_pro_pdf_exemplo.pdf>")
    else:
        calibrate(sys.argv[1])
