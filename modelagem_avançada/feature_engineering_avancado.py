import pandas as pd
import numpy as np
from pathlib import Path

# ============================================================
# ETAPA 1 — CARREGAMENTO E PREPARAÇÃO
# ============================================================
print(" 🚀 Iniciando Engenharia de Features Avançada...")

# Tenta carregar a base final da etapa anterior
arquivo_entrada = "data/base_com_features_FINAL.csv"
try:
    df = pd.read_csv(arquivo_entrada)
except FileNotFoundError:
    try:
        df = pd.read_csv("data/base_com_features.csv")
        print(" ⚠️ Aviso: Usando 'data/base_com_features.csv' (versão anterior).")
    except FileNotFoundError:
        raise FileNotFoundError("❌ ERRO: Arquivo base não encontrado.")

# Garantir tipos corretos de data
df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'])
# Ordenar é fundamental para o cálculo de dias de descanso
df = df.sort_values(by=['TEAM_NAME', 'GAME_DATE']).reset_index(drop=True)

print(f" ✅ Base carregada: {len(df)} registros.")

# ============================================================
# ETAPA 2 — CRIAÇÃO DE FEATURES CONTEXTUAIS
# ============================================================
print("\n ⚙️ Criando Features Contextuais (Casa e Fadiga)...")

# --- 2.1 Fator Casa (IS_HOME) ---
# Lógica: 'vs.' indica mandante (Casa), '@' indica visitante (Fora).
df['IS_HOME'] = df['MATCHUP'].apply(lambda x: 1 if 'vs.' in str(x) else 0)

# --- 2.2 Back-to-Back (IS_B2B) ---
# Calcula a diferença de dias entre o jogo atual e o anterior do mesmo time
df['DAYS_REST'] = df.groupby('TEAM_NAME')['GAME_DATE'].diff().dt.days

# Se DAYS_REST for NaN (primeiro jogo da temporada), assumimos descanso longo (ex: 7 dias)
df['DAYS_REST'] = df['DAYS_REST'].fillna(7)

# Se o descanso for de apenas 1 dia, é um Back-to-Back (cansado)
df['IS_B2B'] = (df['DAYS_REST'] == 1).astype(int)

print(f"   -> Jogos em Casa identificados: {df['IS_HOME'].sum()}")
print(f"   -> Jogos em Back-to-Back (B2B) identificados: {df['IS_B2B'].sum()}")


# ============================================================
# ETAPA 3 — CRIAÇÃO DE FEATURES DIFERENCIAIS (Time vs Oponente)
# ============================================================
print("\n ⚔️ Criando Features Diferenciais (Time - Oponente)...")

# Identifica as colunas de média que queremos comparar
cols_mean = [col for col in df.columns if '_MEAN' in col]

# Para calcular o diferencial, precisamos cruzar o time com seu oponente no mesmo jogo.
# Estratégia: Self-Merge (Unir a tabela com ela mesma pelo GAME_ID)

# 1. Subconjunto apenas com as stats necessárias
df_stats = df[['GAME_ID', 'TEAM_NAME'] + cols_mean].copy()

# 2. Merge: Isso cria combinações para cada jogo (Time A vs Time B)
# suffixes=('', '_OPP') adiciona _OPP nas colunas do oponente
df_merged = pd.merge(df, df_stats, on='GAME_ID', suffixes=('', '_OPP'))

# 3. Filtragem: O merge cria linhas onde Time A joga contra Time A. Removemos isso.
# Queremos apenas a linha onde o time principal é diferente do time da estatística _OPP
df_final = df_merged[df_merged['TEAM_NAME'] != df_merged['TEAM_NAME_OPP']].copy()

# 4. Cálculo Matemático do Diferencial
# Ex: PTS_DIFF = Média do Time - Média do Oponente
new_diff_cols = []
for col in cols_mean:
    new_col_name = col.replace('_MEAN', '_DIFF') # Ex: PTS_MEAN -> PTS_DIFF
    col_opp = f"{col}_OPP"
    
    # Calcula a diferença
    df_final[new_col_name] = df_final[col] - df_final[col_opp]
    new_diff_cols.append(new_col_name)

# 5. Limpeza: Remove as colunas _OPP e duplicatas de merge
cols_to_drop = [c for c in df_final.columns if c.endswith('_OPP')]
df_final.drop(columns=cols_to_drop, inplace=True)
# Garante unicidade
df_final = df_final.drop_duplicates(subset=['GAME_ID', 'TEAM_NAME'])

print(f"   -> Features diferenciais criadas: {len(new_diff_cols)} novas colunas.")
print(f"   -> Exemplo: 'PTS_DIFF' (Positivo = Ataque melhor que a defesa do oponente)")

# ============================================================
# ETAPA 4 — EXPORTAÇÃO PARA EXCEL E CSV
# ============================================================
print("\n 💾 Exportando resultados...")

out_dir = Path(".")
out_dir.mkdir(parents=True, exist_ok=True)

# Nomes dos arquivos
arquivo_csv = out_dir / "data/base_com_features_ENRICHED.csv"
arquivo_excel = out_dir / "data/base_dados_avancada.xlsx"

# Exporta CSV (para uso nos scripts Python)
df_final.to_csv(arquivo_csv, index=False)

# Exporta Excel (para visualização humana, conforme solicitado)
try:
    with pd.ExcelWriter(arquivo_excel, engine='openpyxl') as writer:
        df_final.to_excel(writer, sheet_name='Base_Enriquecida', index=False)
        
        # Cria uma aba de Dicionário de Dados para facilitar leitura
        dict_data = {
            'Variavel': ['IS_HOME', 'IS_B2B', '..._DIFF'],
            'Descricao': [
                '1 se o time joga em casa, 0 se joga fora',
                '1 se o time jogou no dia anterior (fadiga), 0 caso contrário',
                'Diferença entre a média do time e a média do oponente (Time - Oponente)'
            ]
        }
        pd.DataFrame(dict_data).to_excel(writer, sheet_name='Dicionario', index=False)
        
    print(f" ✅ Arquivo Excel gerado: {arquivo_excel.name}")
    print(f" ✅ Arquivo CSV gerado: {arquivo_csv.name}")

except Exception as e:
    print(f" ❌ Erro na exportação Excel: {e}")
    print("    (O CSV foi salvo corretamente)")

print("\n 🏁 Processo concluído. Próximo passo: Rodar a Regressão Logística com as novas variáveis.")