import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

def generate_reports(resultados_alunos, output_dir):
    """
    Recebe uma lista de dicionários contendo os dados e notas de cada aluno.
    Gera um relatório CSV e um gráfico de barras médio por área.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    if not resultados_alunos:
        print("Nenhum resultado para gerar relatório.")
        return
        
    df = pd.DataFrame(resultados_alunos)
    
    # 1. Salvar CSV estruturado
    csv_path = os.path.join(output_dir, "relatorio_notas.csv")
    df.to_csv(csv_path, index=False, encoding='utf-8')
    print(f"Relatório CSV gerado em: {csv_path}")
    
    # Expandir colunas de acerto por área caso não estejam flat no df
    # Assume-se que 'acertos_area' é um dict dentro da list de dicts original.
    # Vamos criar um DataFrame só das áreas para facilitar o plot.
    
    areas_list = []
    for aluno in resultados_alunos:
        if 'acertos_area' in aluno:
            areas_list.append(aluno['acertos_area'])
            
    if areas_list:
        df_areas = pd.DataFrame(areas_list)
        medias_area = df_areas.mean()
        
        # 2. Gerar Gráfico de Médias por Área da Turma
        plt.figure(figsize=(10, 6))
        medias_area.plot(kind='bar', color=['skyblue', 'lightgreen', 'salmon', 'orange'])
        plt.title('Média de Acertos por Área do Conhecimento (Turma)')
        plt.ylabel('Média de Acertos')
        plt.xlabel('Disciplinas / Áreas')
        plt.xticks(rotation=15)
        plt.tight_layout()
        grafico_path = os.path.join(output_dir, "grafico_medias_areas.png")
        plt.savefig(grafico_path)
        plt.close()
        print(f"Gráfico geral gerado em: {grafico_path}")
        
        # 3. Gerar Gráfico de Acertos Totais por aluno
        plt.figure(figsize=(12, 6))
        nomes = df['nome'].apply(lambda x: x if x else "Desconhecido").astype(str)
        # Se os nomes forem muito grandes, pegar só o primeiro nome
        nomes_curtos = nomes.apply(lambda x: x.split(" ")[0] if " " in x else x)
        
        plt.bar(nomes_curtos, df['acertos_total'], color='purple')
        plt.title('Acertos Totais por Aluno')
        plt.ylabel('Pontuação Total')
        plt.xlabel('Aluno')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        grafico_totais_path = os.path.join(output_dir, "grafico_total_por_aluno.png")
        plt.savefig(grafico_totais_path)
        plt.close()
        print(f"Gráfico de totais por aluno gerado em: {grafico_totais_path}")
        
        # 4. Cálculo dos Destaques (Melhor da turma)
        destaques_path = os.path.join(output_dir, "destaques_turma.txt")
        with open(destaques_path, "w", encoding="utf-8") as file:
            file.write("====== RELATÓRIO DE DESTAQUES DA TURMA ======\n\n")
            
            # Melhor aluno geral
            if not df.empty and 'acertos_total' in df.columns:
                idx_melhor_geral = df['acertos_total'].idxmax()
                melhor_geral = df.loc[idx_melhor_geral]
                file.write(f"-> MELHOR ALUNO GERAL:\n")
                file.write(f"   Nome: {melhor_geral['nome']}\n")
                file.write(f"   Acertos Totais: {melhor_geral['acertos_total']}\n\n")
            
            # Melhor aluno por área
            file.write("-> MELHORES ALUNOS POR ÁREA:\n")
            areas_cols = [col for col in df.columns if col.startswith('acertos_') and col not in ['acertos_total', 'acertos_area']]
            for col in areas_cols:
                nome_area = col.replace("acertos_", "").replace("_", " ")
                idx_melhor_area = df[col].idxmax()
                melhor_aluno_area = df.loc[idx_melhor_area]
                file.write(f"   - {nome_area}: {melhor_aluno_area['nome']} ({melhor_aluno_area[col]} acertos)\n")
        
        print(f"Relatório de destaques salvo em: {destaques_path}")
        
        # 5. Gráfico de Desempenho Completo (Acertos Totais E Por Área via Barras Empilhadas)
        # Vamos usar as áreas empilhadas que somam o total
        if areas_cols:
            df_plot_empilhado = df[['nome'] + areas_cols].copy()
            df_plot_empilhado['nome'] = nomes_curtos.values
            df_plot_empilhado.set_index('nome', inplace=True)
            
            # Limpar nomes de colunas para o grafico
            df_plot_empilhado.columns = [c.replace("acertos_", "").replace("_", " ") for c in df_plot_empilhado.columns]
            
            ax = df_plot_empilhado.plot(kind='bar', stacked=True, figsize=(14, 7), colormap='viridis')
            plt.title('Desempenho por Aluno (Visão por Áreas)')
            plt.ylabel('Acertos Totais / Acumulados')
            plt.xlabel('Aluno')
            plt.xticks(rotation=45, ha='right')
            
            # Adiciona os totais acima da barra
            for i, total in enumerate(df['acertos_total']):
                ax.text(i, total + 0.5, str(total), ha='center', va='bottom', fontweight='bold')
                
            plt.tight_layout()
            grafico_empilhado_path = os.path.join(output_dir, "grafico_desempenho_completo_turma.png")
            plt.savefig(grafico_empilhado_path)
            plt.close()
            print(f"Gráfico completo de áreas empilhadas gerado em: {grafico_empilhado_path}")
            
        # 6. Gerar Gráfico Individual para cada aluno (por área)
        pasta_individuais = os.path.join(output_dir, "graficos_individuais")
        if not os.path.exists(pasta_individuais):
            os.makedirs(pasta_individuais)
            
        for i, aluno in enumerate(resultados_alunos):
            nome_aluno = aluno.get('nome', f'Aluno_{i+1}')
            
            # Padronização de String (Snake Case)
            nome_arquivo = nome_aluno.lower().strip()
            # Mantém apenas alfa-numéricos, troca o resto por _
            nome_arquivo = "".join(c if c.isalnum() else "_" for c in nome_arquivo)
            # Remove underlines duplicados para ficar elegante
            while "__" in nome_arquivo:
                nome_arquivo = nome_arquivo.replace("__", "_")
            nome_arquivo = nome_arquivo.strip("_") # Limpa as pontas
            
            if not nome_arquivo:
                nome_arquivo = f"aluno_{i+1}"
                
            acertos_area = aluno.get('acertos_area', {})
            if not acertos_area:
                continue
                
            plt.figure(figsize=(8, 5))
            areas = list(acertos_area.keys())
            valores = list(acertos_area.values())
            
            # Gráfico de barras horizontais
            plt.barh(areas, valores, color=['#4dc9f6', '#f67019', '#f53794', '#537bc4'])
            plt.title(f'Desempenho de: {nome_aluno}')
            plt.xlabel('Acertos')
            plt.xlim(0, max(max(valores) + 1, 6)) # Max 6 acertos por área no gabarito
            plt.tight_layout()
            
            ind_path = os.path.join(pasta_individuais, f"desempenho_{nome_arquivo}.png")
            plt.savefig(ind_path)
            plt.close()
            
        print(f"Foram gerados {len(resultados_alunos)} gráficos individuais na pasta: {pasta_individuais}")
