import pandas as pd
import numpy as np
import statsmodels.api as sm
from pathlib import Path

# ============================================================
# ETAPA 1 — PREPARAÇÃO
# ============================================================
print(" 💰 Iniciando Simulação Financeira com Classificação de Risco...")

try:
    df = pd.read_csv("data/base_com_features_ENRICHED.csv")
except FileNotFoundError:

    raise FileNotFoundError("❌ ERRO: Base enriquecida não encontrada.")

df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'])
df['YEAR'] = df['GAME_DATE'].dt.year
df['VITORIA'] = pd.to_numeric(df['VITORIA'], errors='coerce')

# Variáveis do Modelo Campeão
vars_modelo = [
    'IS_HOME', 'IS_B2B', 
    'PTS_DIFF', 'REB_DIFF', 'AST_DIFF', 'STL_DIFF', 'BLK_DIFF', 'TOV_DIFF',
    'FG_PCT_DIFF', 'FT_PCT_DIFF', 'FG3_PCT_DIFF'
]

# Limpeza
colunas = ['GAME_DATE', 'YEAR', 'TEAM_NAME', 'MATCHUP', 'VITORIA'] + vars_modelo
df_modelo = df[colunas].copy().dropna()

# ============================================================
# ETAPA 2 — TREINAMENTO E PREVISÃO (Cenário 2025)
# ============================================================
print(" ⚙️  Gerando probabilidades para 2025...")

mask_train = df_modelo['YEAR'].isin([2023, 2024])
mask_test = df_modelo['YEAR'].isin([2025])

X_treino = sm.add_constant(df_modelo.loc[mask_train, vars_modelo])
Y_treino = df_modelo.loc[mask_train, 'VITORIA']
X_teste = sm.add_constant(df_modelo.loc[mask_test, vars_modelo])

# Ajuste do Modelo
modelo = sm.Logit(Y_treino, X_treino).fit(disp=False)
# Probabilidade Real (0 a 1)
probs = modelo.predict(X_teste)

# Base de Apostas
df_apostas = df_modelo.loc[mask_test].copy()
df_apostas['Prob_Modelo'] = probs

# ============================================================
# ETAPA 3 — CRIAÇÃO DO MERCADO (ODDS)
# ============================================================
# Simulando odds realistas com base na probabilidade do modelo + Ruído de Mercado
np.random.seed(42)

# O mercado erra um pouco (Ruído) e cobra uma taxa (Vig)
ruido = np.random.normal(0, 0.03, len(df_apostas)) # 3% de erro padrão do mercado
prob_mercado = df_apostas['Prob_Modelo'] + ruido
prob_mercado = prob_mercado.clip(0.05, 0.95) # Trava entre 5% e 95%

# Odd = 1 / Probabilidade * 0.95 (Margem da Casa)
df_apostas['Odd_Casa'] = (1 / prob_mercado) * 0.95
df_apostas['Odd_Casa'] = df_apostas['Odd_Casa'].round(2)

# ============================================================
# ETAPA 4 — CÁLCULO DE VALOR ESPERADO (EV) E CLASSIFICAÇÃO
# ============================================================
print(" 💎 Classificando oportunidades...")

# EV = (Probabilidade Real * Odd) - 1
df_apostas['EV_ROI'] = (df_apostas['Prob_Modelo'] * df_apostas['Odd_Casa']) - 1

# --- LÓGICA DE CLASSIFICAÇÃO (A que vai para o App) ---
def classificar_oportunidade(row):
    ev = row['EV_ROI']
    prob = row['Prob_Modelo']
    
    if ev <= 0:
        return "⛔ NÃO APOSTAR"
    elif prob > 0.65 and ev > 0.10:
        return "💎 OURO (Alta Confiança + Valor)"
    elif prob > 0.55 and ev > 0.05:
        return "🥈 PRATA (Boa Aposta)"
    elif ev > 0.02:
        return "🥉 BRONZE (Valor Marginal)"
    else:
        return "⚠️ NEUTRO (Risco alto)"

df_apostas['Classificacao'] = df_apostas.apply(classificar_oportunidade, axis=1)

# ============================================================
# ETAPA 5 — EXECUÇÃO DAS APOSTAS
# ============================================================
# Regra: Apostamos R$ 100 apenas em Ouro e Prata
df_apostas['Aposta'] = np.where(
    df_apostas['Classificacao'].isin(["💎 OURO (Alta Confiança + Valor)", "🥈 PRATA (Boa Aposta)"]), 
    100, 
    0
)

# Resultado Financeiro
df_apostas['Lucro'] = np.where(
    df_apostas['Aposta'] > 0,
    np.where(df_apostas['VITORIA'] == 1, 
             (df_apostas['Aposta'] * df_apostas['Odd_Casa']) - df_apostas['Aposta'], # Green
             -df_apostas['Aposta']), # Red
    0
)

df_apostas['Banca_Acumulada'] = df_apostas['Lucro'].cumsum()

# ============================================================
# ETAPA 6 — RELATÓRIO FINAL
# ============================================================
lucro_total = df_apostas['Lucro'].sum()
roi = (lucro_total / df_apostas['Aposta'].sum()) * 100 if df_apostas['Aposta'].sum() > 0 else 0
apostas_feitas = len(df_apostas[df_apostas['Aposta'] > 0])

print(f"\n 📊 RESULTADO DA CARTEIRA (2025):")
print(f"    - Jogos Analisados: {len(df_apostas)}")
print(f"    - Apostas Realizadas: {apostas_feitas} (Apenas Ouro e Prata)")
print(f"    - Lucro Líquido:    R$ {lucro_total:.2f}")
print(f"    - ROI (Retorno):    {roi:.2f}%")

print("\n 📋 Distribuição das Recomendações:")
print(df_apostas['Classificacao'].value_counts())

# Exportar
arquivo_excel = "data/relatorio_financeiro_classificado.xlsx"
try:
    with pd.ExcelWriter(arquivo_excel, engine='openpyxl') as writer:
        df_apostas.to_excel(writer, sheet_name='Apostas_Detalhadas', index=False)
        
        # Resumo por Classificação
        resumo = df_apostas.groupby('Classificacao')[['Aposta', 'Lucro']].sum().sort_values(by='Lucro', ascending=False)
        resumo.to_excel(writer, sheet_name='Performance_por_Classe')
        
    print(f"\n 💾 Arquivo gerado: {arquivo_excel}")
    print("    (Contém as recomendações prontas para o App)")

except Exception as e:
    print(f"Erro ao salvar: {e}")