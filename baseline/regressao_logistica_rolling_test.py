import pandas as pd
import numpy as np
import statsmodels.api as sm
from pathlib import Path
from sklearn.metrics import accuracy_score, roc_auc_score

# ============================================================
# ETAPA 1 — PREPARAÇÃO DA BASE PARA MODELAGEM
# ============================================================
print(" 🚀 Iniciando Modelagem Econométrica e Validação Preditiva")

# Carrega a base com as features (médias acumuladas)
arquivo_features = "data/base_com_features_FINAL.csv"
try:
    df = pd.read_csv(arquivo_features)
except FileNotFoundError:
    try:
        df = pd.read_csv("data/base_com_features.csv")
    except FileNotFoundError:
        raise FileNotFoundError("❌ ERRO: O arquivo de features não foi encontrado. Certifique-se de que a etapa de análise descritiva foi executada.")

# Converter GAME_DATE para datetime para filtragem de ano
df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'], errors='coerce')
df['YEAR'] = df['GAME_DATE'].dt.year

# Define as variáveis preditoras de média acumulada (MEAN)
vars_desempenho = [
    'PTS_MEAN', 'REB_MEAN', 'AST_MEAN', 'STL_MEAN', 'BLK_MEAN', 'TOV_MEAN',
    'FG_PCT_MEAN', 'FT_PCT_MEAN', 'FG3_PCT_MEAN', 
]

# === 1.1 Limpeza e Seleção ===
df['VITORIA'] = pd.to_numeric(df['VITORIA'], errors='coerce')
colunas_modelo = ['VITORIA', 'YEAR'] + [col for col in vars_desempenho if col in df.columns]
df_modelo = df[colunas_modelo].dropna()

if df_modelo.shape[0] == 0:
    print(" ❌ ERRO: O DataFrame está vazio após a limpeza de NaNs. Verifique os dados originais.")
    exit()

# === 1.2 DEFINIÇÃO DOS CENÁRIOS DE TESTE (Rolling + Geral) ===
scenarios = {
    "Cenario_A (Treino_22_23, Teste_24)": {
        'Train_Years': [2022, 2023],
        'Test_Years': [2024]
    },
    "Cenario_B (Treino_23_24, Teste_25)": {
        'Train_Years': [2023, 2024],
        'Test_Years': [2025]
    },
    "Cenario_C (Treino_22_23_24, Teste_25)": {
        'Train_Years': [2022, 2023, 2024],
        'Test_Years': [2025]
    },
    "Cenario_Geral (Treino_Total, Teste_Total)": {
        'Train_Years': [2022, 2023, 2024, 2025],
        'Test_Years': [2022, 2023, 2024, 2025]
    }
}

# Dicionários para armazenar os resultados de cada cenário
resultados_coefs = {}
resultados_odds = {}
resultados_metricas = {}

print(f" ✅ Base pronta para modelagem: {df_modelo.shape[0]} observações.")
print(" ---------------------------------------------------------------")

# ============================================================
# ETAPA 2 — LOOP DE AJUSTE, VALIDAÇÃO E EXPORTAÇÃO
# ============================================================

for scenario_name, years in scenarios.items():
    
    print(f"\n ⚙️  EXECUTANDO: {scenario_name}")
    
    # === 2.1 Separação Treino e Teste (Baseado no Ano/Cenário) ===
    df_treino = df_modelo[df_modelo['YEAR'].isin(years['Train_Years'])]
    df_teste = df_modelo[df_modelo['YEAR'].isin(years['Test_Years'])]

    X_treino = df_treino[[col for col in vars_desempenho]]
    Y_treino = df_treino['VITORIA']
    
    X_teste = df_teste[[col for col in vars_desempenho]]
    Y_teste = df_teste['VITORIA']

    print(f"    - Treino: {X_treino.shape[0]} | Teste: {X_teste.shape[0]}")

    if X_treino.shape[0] == 0 or X_teste.shape[0] == 0:
        print(f" ⚠️  AVISO: Faltam dados para o {scenario_name}. Pulando este cenário.")
        continue

    # === 2.2 Ajuste do Modelo Logit (Statsmodels) ===
    X_treino_sm = sm.add_constant(X_treino)
    X_teste_sm = sm.add_constant(X_teste)

    try:
        modelo_logit = sm.Logit(Y_treino, X_treino_sm)
        resultado = modelo_logit.fit(disp=False)
    except Exception as e:
        print(f" ❌ ERRO ao ajustar o modelo Logit: {e}")
        continue

    # === 2.3 Validação Preditiva (Métricas) ===
    probabilidades_teste = resultado.predict(X_teste_sm)
    Y_previsto = (probabilidades_teste >= 0.5).astype(int)

    acuracia = accuracy_score(Y_teste, Y_previsto)
    auc = roc_auc_score(Y_teste, probabilidades_teste)

    metricas_df = pd.DataFrame({
        'Métrica': ['Acurácia (Teste)', 'AUC (Teste)', 'Amostras de Teste'],
        'Valor': [acuracia, auc, len(Y_teste)]
    }).set_index('Métrica')
    
    # === 2.4 (CORRIGIDO) Preparação das Tabelas (Manual) ===
    # Esta é a correção para o erro 'AttributeError'
    
    # 1. Tabela de Coeficientes e P-Values
    coefs_df = pd.DataFrame({
        'coef': resultado.params,
        'std err': resultado.bse,
        't': resultado.tvalues,
        'P>|t|': resultado.pvalues,
        '[0.025': resultado.conf_int()[0],
        '0.975]': resultado.conf_int()[1]
    })

    # 2. Tabela de Odds Ratios
    odds_df = pd.DataFrame({
        'Odds Ratio (e^Coef)': np.exp(resultado.params),
        'P-Value': resultado.pvalues
    }).round(4)

    # Armazena os resultados nos dicionários
    resultados_coefs[scenario_name] = coefs_df.round(4)
    resultados_odds[scenario_name] = odds_df
    resultados_metricas[scenario_name] = metricas_df.round(4)
    
    print(f"    - Acurácia (Teste): {acuracia:.4f} | AUC (Teste): {auc:.4f}")

print("\n 🎯 Modelagem e Validação Concluídas.")