import os
import json
import cv2
import PIL.Image
from google import genai
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env (onde deve estar GEMINI_API_KEY)
load_dotenv()

def extract_header_with_ai(image):
    """
    Usa o modelo Multimodal Gemini (3.1 Flash Lite) para ler o cabeçalho com Inteligência Artificial.
    Recebe um frame NumPy do OpenCV e envia pro Google GenAI.
    """
    # Converter opencv BGR para RGB e criar PIL Image para o Gemini não dar erro
    img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_image = PIL.Image.fromarray(img_rgb)
    
    # Prompt focado em forçar saída estruturada
    prompt = """
    Voce é um assistente de OCR escolar focado em ler letra de mão.
    Encontre os dados descritos no cabeçalho e transcreva-os com exatidão.
    
    REGRA CRÍTICA: Extraia APENAS o valor/conteúdo preenchido pelo aluno.
    NÃO inclua os rótulos que já estão impressos no papel (ex: NÃO retorne 'ALUNO: JOÃO', 'Nome: ', 'Turma: ', retorne apenas o valor preenchido 'JOÃO').
    NÃO coloque aspas, traços ou hifens no meio ou no início do nome. Quero apenas as letras "JOAO".
    
    Retorne APENAS um JSON válido e puro, com EXATAMENTE estas chaves em minúsculo:
    "municipio", "escola", "ano", "turma", "bimestre", "nome".
    Se o aluno não preencheu, deixe como "".
    NAO escreva ```json na resposta. Retorne puramente o objeto {...}.
    """
    
    # O cliente pega automaticamente a chave de GEMINI_API_KEY no seu ambiente .env
    client = genai.Client()
    
    # Lista de prioridade em cascata se algum modelo bater a cota (ex: 503 Unavailable ou 429 RateLimit)
    modelos_disponiveis = [
        'gemini-3.1-flash-lite-preview',
        'gemini-2.0-flash',
        'gemini-2.5-flash',
        'gemini-1.5-flash'
    ]
    
    response = None
    for model_name in modelos_disponiveis:
        try:
            print(f"      [Fallback IA] Conectando com a API Multimodal do Gemini (Buscando: {model_name})...")
            response = client.models.generate_content(
                model=model_name,
                contents=[prompt, pil_image]
            )
            print(f"      [Sucesso na IA] Conectado usando {model_name}!")
            break # Deu certo, encerra o loop de tentativas!
        except Exception as e:
            print(f"      [Falha - {model_name}] Modelo indisponível ou estourou cota: {e}. Tentando o próximo...")
            
    if not response:
        raise Exception("Esgotados todos os modelos de Inteligência Artificial para Fallback.")
        
    txt = response.text.strip()
    txt = txt.removeprefix('```json').removesuffix('```').strip()
    
    try:
        dados = json.loads(txt)
        
        # Super sanitização via Python para remover lixos residuais (-, aspas)
        for k, v in dados.items():
            if isinstance(v, str):
                 dados[k] = v.strip(" -'\"")
                 
        return dados
    except json.JSONDecodeError:
        print(f"      [Fallback IA] Erro ao decodificar JSON. Retorno puro: {txt}")
        # Retorna algo neutro caso a IA tenha alucinado
        return {
            "municipio": "",
            "escola": "",
            "ano": "",
            "turma": "",
            "bimestre": "",
            "nome": "Erro Leitura IA"
        }

def extract_answers_with_ai(image):
    """
    Lê as bolhas do gabarito (1 a 24) através da Inteligência Artificial.
    Acionado quando a geometria OMR falha devido a inclinação extrema na câmera/scanner.
    """
    img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_image = PIL.Image.fromarray(img_rgb)
    
    prompt = """
    A imagem é um cartão de respostas de prova (gabarito).
    Existem 24 questões numeradas de 1 a 24, organizadas em colunas.
    Verifique exatamente qual bolha (A, B, C ou D) foi PINTADA/MARCADA pelo aluno em CADA questão.
    
    Retorne APENAS um objeto JSON. 
    Chaves: "1" a "24" em string pura.
    Valores: a letra marcada "A", "B", "C" ou "D", maiúscula. 
    REGRAS CRÍTICAS DE PREENCHIMENTO:
    - Se nenhuma alternativa estiver pintada na questão, indique "X".
    - Se mais de uma alternativa estiver pintada ou a questão estiver riscada/rasurada, indique "ANULADA".
    
    NAO DEVOLVA MAIS NADA. NÃO USE ```json. SÓ '{...}' PURO!
    """
    
    client = genai.Client()
    modelos_disponiveis = [
        'gemini-3.1-flash-lite-preview',
        'gemini-2.0-flash',
        'gemini-2.5-flash',
        'gemini-1.5-flash'
    ]
    
    response = None
    for model_name in modelos_disponiveis:
        try:
            print(f"      [Resgate OMR IA] Lendo gabarito torto com {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=[prompt, pil_image]
            )
            print(f"      [Sucesso OMR IA] Gabarito lido!")
            break
        except Exception as e:
            pass
            
    if not response:
        print("      [Falha Crítica OMR] IA indisponível para ler página torta.")
        return {str(i):"" for i in range(1,25)}
        
    txt = response.text.strip().removeprefix('```json').removesuffix('```').strip()
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        print("      [Erro] IA alucinou forado do JSON no gabarito.")
        return {str(i):"" for i in range(1,25)}
