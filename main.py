import os
import json
from src.pdf_processor import convert_pdf_to_images
from src.qr_reader import read_matricula
from src.ocr_reader import extract_header_info
from src.omr_processor import read_answers
from src.evaluator import evaluate_student
from src.reporter import generate_reports

def load_official_answers(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def process_pdf(pdf_path, gabarito_oficial):
    print(f"Processando arquivo: {pdf_path}")
    images = convert_pdf_to_images(pdf_path, dpi=300)
    resultados = []
    
    for idx, img in enumerate(images):
        print(f"  Analisando página {idx+1}")
        
        # 1. Extração QR Code
        qr_data = read_matricula(img)
        matricula = qr_data
        
        # 2. Extração OCR Cabeçalho
        cabecalho_bruto = extract_header_info(img)
        
        # Usar dados 100% precisos do QR Code se disponível (ID|ANO|BIMESTRE|??|TURMA)
        if qr_data and "|" in qr_data:
            partes = qr_data.split("|")
            matricula = partes[0]
            if len(partes) >= 3:
                cabecalho_bruto["ano"] = partes[1]
                cabecalho_bruto["bimestre"] = partes[2]
            if len(partes) >= 5:
                cabecalho_bruto["turma"] = partes[4]
                
        # Super-Padronização de Caixa Alta (UPPERCASE) para TODOS os dados
        cabecalho = {}
        for k, v in cabecalho_bruto.items():
            if isinstance(v, str):
                cabecalho[k] = v.upper()
            else:
                cabecalho[k] = v
        
        # 3. Leitura OMR Gabarito (bolhas)
        # Se a página estava torta a ponto da IA ter sido ativada pro cabecalho,
        # a matematica de bolhas do OpenCV vai falhar. Então usamos a IA pras bolhas tambem!
        if cabecalho.get("_usou_ia"):
            from src.multimodal_reader import extract_answers_with_ai
            respostas = extract_answers_with_ai(img)
        else:
            respostas = read_answers(img)
        
        # 4. Avaliação
        avaliacao = evaluate_student(respostas, gabarito_oficial)
        
        # Consolidar dados do aluno
        aluno_dados = {
            "pagina_pdf": idx + 1,
            "matricula": matricula,
            "nome": cabecalho.get("nome", "Desconhecido"),
            "municipio": cabecalho.get("municipio", ""),
            "escola": cabecalho.get("escola", ""),
            "ano": cabecalho.get("ano", ""),
            "turma": cabecalho.get("turma", ""),
            "bimestre": cabecalho.get("bimestre", ""),
            "acertos_total": avaliacao["acertos_total"],
            "acertos_area": avaliacao["acertos_area"] # Para o repórter
        }
        
        # Opend para transformar áreas em colunas diretas no CSV final
        for area, pts in avaliacao["acertos_area"].items():
            aluno_dados[f"acertos_{area.replace(' ', '_')}"] = pts
            
        resultados.append(aluno_dados)
        
    return resultados

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(base_dir, "data", "input")
    output_dir = os.path.join(base_dir, "data", "output")
    gabarito_path = os.path.join(base_dir, "data", "gabarito_oficial.json")
    
    gabarito_oficial = load_official_answers(gabarito_path)
    todos_resultados = []
    
    # Processar todos os PDFs na pasta de input
    if not os.path.exists(input_dir):
        print(f"Crie a pasta {input_dir} e coloque arquivos PDF lá.")
        return
        
    for p_file in os.listdir(input_dir):
        if p_file.lower().endswith(".pdf"):
            full_path = os.path.join(input_dir, p_file)
            res = process_pdf(full_path, gabarito_oficial)
            todos_resultados.extend(res)
            
    # Gerar relatórios
    if todos_resultados:
        generate_reports(todos_resultados, output_dir)
        print("Processamento finalizado com sucesso. Cheque a pasta data/output/.")
    else:
        print("Nenhum dado processado.")

if __name__ == "__main__":
    main()
