def evaluate_student(respostas_aluno, gabarito_oficial):
    """
    Compara o dicionário de respostas lidas (OMR) com o gabarito oficial JSON.
    Retorna a pontuação total e por área.
    """
    resultado = {
        "acertos_total": 0,
        "acertos_area": {},
        "detalhes": {}
    }
    
    oficial_resps = gabarito_oficial["respostas"]
    areas = gabarito_oficial["areas"]
    
    # Inicializar contadores por área
    for area in areas.keys():
        resultado["acertos_area"][area] = 0
        
    for q_str, resp_aluno in respostas_aluno.items():
        correta = oficial_resps.get(q_str, None)
        acertou = (resp_aluno == correta)
        
        # Acha a área dessa questão
        area_questao = None
        for area_name, q_list in areas.items():
            if int(q_str) in q_list:
                area_questao = area_name
                break
                
        resultado["detalhes"][q_str] = {
            "marcada": resp_aluno,
            "correta": correta,
            "acertou": acertou,
            "area": area_questao
        }
        
        if acertou:
            resultado["acertos_total"] += 1
            if area_questao:
                resultado["acertos_area"][area_questao] += 1
                
    return resultado
