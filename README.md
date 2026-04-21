# Leitor de Gabaritos Escolares Híbrido (OMR + IA)

Este projeto foi desenvolvido como atividade prática para automatizar a leitura de gabaritos de provas escolares. A solução adota uma abordagem híbrida, combinando processamento local de imagens (Visão Computacional) com auxílio de Inteligência Artificial Multimodal para lidar com anomalias de escaneamento e caligrafia.

## Arquitetura e Decisões Técnicas

O fluxo de processamento foi desenhado para ser eficiente e autônomo, reduzindo ao máximo a latência e dependência de serviços externos:
*   **Processamento Primário (Offline):** Utiliza OpenCV para leitura óptica de marcas (OMR) no processamento matemático das bolhas de resposta. Para a leitura de cabeçalhos impressos (nome, turma, etc) o Tesseract OCR  é utilizado.
*   **Fallback com IA (Cloud):** Caso a confiança da leitura do Tesseract caia de forma abrupta (indicativo de preenchimento manuscrito irregular) ou as coordenadas geométricas das bolhas falhem (scanner inclinado), o frame é escalonado via modelo Multimodal do Google (Gemini) para uma extração cognitiva da imagem.
*   **Eliminação de Dependências:** O parseamento do PDF para matrizes de imagem foi implementado via `PyMuPDF` (`fitz`), o que evita exigir a instalação de bibliotecas de sistema C++ como o `poppler` em ambientes Windows (necessário caso usássemos a biblioteca `zerox`).

---

## Estrutura do Código e Módulos

O sistema conta com dois utilitários de nível raiz (ferramental de suporte) e o núcleo empacotado na pasta `src/`:

### 🛠️ Módulos de Suporte (Raiz)
*   **`main.py`**
    Script principal de orquestração. Gerencia o fluxo de entrada iterando sobre o PDF, invocando os demais módulos, padronizando os tipos de dados do dicionário resultante (como *upper_case* em strings) e chamando os métodos finais de avaliação e exportação.

*   **`debug_layout.py`**
    Uma poderosa ferramenta visual de calibração espacial. Desenha _bounding boxes_ (retângulos vermelhos e verdes) na exata coordenada geométrica simulada pelo algoritmo para checagem matemática humana. Ajuda a diagnosticar se o código está "mirando" milimetricamente nos gabaritos e bolhas A, B, C e D calculadas, sem rodar OCR denso.

*   **`calibrate.py`**
    Script auxiliar que permite ao mantenedor recortar e gerar os *offsets* iniciais e definitivos para um novo molde de prova através de calibração manual por eixos.

### 🧠 Núcleo de Processamento (`src/`)

*   **`src/pdf_processor.py`**
    Módulo responsável por converter o arquivo `Image_101.pdf` em matrizes de imagem manipuláveis (via `PyMuPDF / fitz`) com um DPI fixo (300) para preservar os pixels limpos para os próximos algoritmos.

*   **`src/qr_reader.py`**
    Utiliza as detecções do `pyzbar` para localizar e extrair dados encodados como a *Matrícula* lendo os códigos QR de cada folha processada.

*   **`src/ocr_reader.py`**
    Trata o cabeçalho. Seleciona dinamicamente Regiões de Interesse (ROIs) definidas em configuração e aplica o pacote Tesseract local. 
    Contém *heurísticas lógicas anti-alucinação* (strip de caracteres, validações numéricas) que previnem que sujeira lida pelo motor vire dado falso. Se a acurácia de leitura cair em relação à média local estipulada, ele passa a folha atual para a o módulo de IA processar.

*   **`src/multimodal_reader.py`**
    A camada de "Resgate". Um script contendo as rotas de API da biblioteca nativa `google-genai`. Ele engloba a engenharia de prompt para instruir o modelo (`gemini-3.1-flash-lite`, `gemini-2.5-flash` em sistema de fallback array estruturado) a retornar JSONs com os dados brutos da folha de teste manuscrita.

*   **`src/omr_processor.py`**
    O Leitor Óptico. Percorre as 24 questões através de cálculos preditivos de distância vertical e horizontal (Offset). Aplica uma técnica `Gaussian Blur` seguida de Binarização (`Otsu thresholding`) para identificar se a contagem de pixels pretos (tinta) de uma bolha ultrapassou a tolerância predefinida. Classifica questões em branco com erro `X` e questões rasuradas múltiplas como `ANULADA`.

*   **`src/config.py`**
    Armazena váriaveis globais constantes como os eixos de corte matemáticos do cabeçalho e calibração fina das bolhas por coluna.

*   **`src/evaluator.py`**
    Cruza as respostas retornadas do módulo OMR/IA contra a estrutura real contida em `gabarito_oficial.json`, agrupando acertos e perdas de acordo com a área do conhecimento solicitada (Ex: Português 1-6, Matemática 7-12).
    
*   **`src/reporter.py`**
    Recebe as consolidações JSON e empacota toda a análise usando `pandas` e `matplotlib`, finalizando com o despejo no diretório `data/output/` em 4 frentes:
    - `relatorio_notas.csv`: Base de dados tabulada final com chaves limpas em caixa-alta.
    - `destaques_turma.txt`: Avaliação lógica de alunos com as melhores performances.
    - Gráficos Analíticos Gerais da Turma (Formato normal e Barras empilhadas).
    - `graficos_individuais/`: Pasta de geração de gráficos curtos focados unicamente no usuário aluno.

---

## 🛠️ Como Executar

**1. Instalação de Dependências de Pacote**
```bash
pip install opencv-python pytesseract pyzbar PyMuPDF pandas matplotlib google-genai python-dotenv pillow
```

**2. Verificação de Dependências do Sistema**
O sistema requer o binário instalador executável do **Tesseract OCR** presente/mapeado no diretório da sua máquina Windows:
- Caminho assumido: `C:\Program Files\Tesseract-OCR\tesseract.exe`

**3. Chave de API**
O processo de Fallback via Nuvem necessitará da chave da API Gemini. Crie um arquivo `.env` na raiz espelhando a seguinte estrutura:
```env
GEMINI_API_KEY="AIzaSy...Sua_Chave..."
```

**4. Executando**
Certifique-se de que o PDF de estudantes esteja inserido em `data/input`.
```bash
python main.py
```
