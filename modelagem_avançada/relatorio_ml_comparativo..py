import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False
    print("⚠️ XGBoost não instalado. Rodando apenas Random Forest e LogReg.")

# ============================================================
# ETAPA 1 — PREPARAÇÃO
# ============================================================
print(" 🚀 Iniciando Batalha de Modelos (ML Avançado)...")

arquivo_features = "data/base_com_features_ENRICHED.csv"
try:
    df = pd.read_csv(arquivo_features)
except FileNotFoundError:
    raise FileNotFoundError(f"❌ ERRO: '{arquivo_features}' não encontrado.")

# Tratamento básico
df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'], errors='coerce')
df['YEAR'] = df['GAME_DATE'].dt.year
df['VITORIA'] = pd.to_numeric(df['VITORIA'], errors='coerce')

# Variáveis (Contexto + Diferenciais)
vars_modelo = [
    'IS_HOME', 'IS_B2B', 
    'PTS_DIFF', 'REB_DIFF', 'AST_DIFF', 'STL_DIFF', 'BLK_DIFF', 'TOV_DIFF',
    'FG_PCT_DIFF', 'FT_PCT_DIFF', 'FG3_PCT_DIFF'
]

# Limpeza Profunda (ML não aceita NaNs)
colunas_finais = ['VITORIA', 'YEAR'] + vars_modelo
df_modelo = df[colunas_finais].copy()
df_modelo.replace([np.inf, -np.inf], np.nan, inplace=True)
df_modelo.dropna(inplace=True)

print(f" ✅ Base pronta: {len(df_modelo)} jogos.")

# ============================================================
# ETAPA 2 — DEFINIÇÃO DOS MODELOS E CENÁRIOS
# ============================================================

# Dicionário de Modelos
modelos = {
    'Logistic_Regression': LogisticRegression(solver='liblinear', random_state=42),
    'Random_Forest': RandomForestClassifier(n_estimators=100, min_samples_leaf=5, max_depth=10, random_state=42)
}

if HAS_XGB:
    # Configuração conservadora para evitar overfitting em dados ruidosos como esportes
    modelos['XGBoost'] = XGBClassifier(n_estimators=100, learning_rate=0.05, max_depth=3, random_state=42, eval_metric='logloss')

# Cenários (Rolling Window)
scenarios = {
    "Cenario_A (Teste 24)": {'Train': [2022, 2023], 'Test': [2024]},
    "Cenario_B (Teste 25)": {'Train': [2023, 2024], 'Test': [2025]}, # Nosso foco principal
    "Cenario_Geral": {'Train': [2022, 2023, 2024, 2025], 'Test': [2022, 2023, 2024, 2025]}
}

resultados_gerais = []
feature_importance = []

# ============================================================
# ETAPA 3 — TREINAMENTO E VALIDAÇÃO
# ============================================================

for cenario_nome, years in scenarios.items():
    print(f"\n 🏟️  Rodando: {cenario_nome}")
    
    mask_train = df_modelo['YEAR'].isin(years['Train'])
    mask_test = df_modelo['YEAR'].isin(years['Test'])

    X_treino = df_modelo.loc[mask_train, vars_modelo]
    Y_treino = df_modelo.loc[mask_train, 'VITORIA']
    X_teste = df_modelo.loc[mask_test, vars_modelo]
    Y_teste = df_modelo.loc[mask_test, 'VITORIA']

    if len(X_treino) == 0 or len(X_teste) == 0: continue

    for nome_modelo, clf in modelos.items():
        try:
            # Treino
            clf.fit(X_treino, Y_treino)
            
            # Predição (Probabilidades)
            probs = clf.predict_proba(X_teste)[:, 1] # Pega a chance de Vitória (classe 1)
            preds = (probs >= 0.5).astype(int)
            
            # Métricas
            acc = accuracy_score(Y_teste, preds)
            auc = roc_auc_score(Y_teste, probs)
            
            print(f"    🤖 {nome_modelo:20} -> Acc: {acc:.4f} | AUC: {auc:.4f}")
            
            resultados_gerais.append({
                'Cenario': cenario_nome,
                'Modelo': nome_modelo,
                'Acuracia': acc,
                'AUC': auc,
                'Amostras': len(Y_teste)
            })

            # Salvar Importância das Variáveis (Apenas para RF e XGB)
            if nome_modelo in ['Random_Forest', 'XGBoost']:
                importancias = clf.feature_importances_
                for i, col in enumerate(vars_modelo):
                    feature_importance.append({
                        'Cenario': cenario_nome,
                        'Modelo': nome_modelo,
                        'Feature': col,
                        'Importancia': importancias[i]
                    })

        except Exception as e:
            print(f"    ❌ Erro no {nome_modelo}: {e}")

# ============================================================
# ETAPA 4 — EXPORTAÇÃO
# ============================================================
print("\n 💾 Consolidando resultados...")

df_res = pd.DataFrame(resultados_gerais)
df_feat = pd.DataFrame(feature_importance)

out_dir = Path(".")
arquivo_excel = out_dir / "data/relatorio_ml_comparativo.xlsx"

try:
    with pd.ExcelWriter(arquivo_excel, engine='openpyxl') as writer:
        # 1. Tabela Comparativa (Pivot para facilitar leitura)
        pivot_res = df_res.pivot(index='Cenario', columns='Modelo', values=['Acuracia', 'AUC'])
        pivot_res.to_excel(writer, sheet_name='Comparativo_Modelos')
        
        # 2. Dados Brutos
        df_res.to_excel(writer, sheet_name='Resultados_Brutos', index=False)
        
        # 3. Feature Importance (O que o modelo considera importante?)
        if not df_feat.empty:
            # Pivot para ver a importância por modelo
            pivot_feat = df_feat[df_feat['Cenario'] == 'Cenario_Geral'].pivot_table(
                index='Feature', columns='Modelo', values='Importancia'
            ).sort_values(by='XGBoost' if HAS_XGB else 'Random_Forest', ascending=False)
            pivot_feat.to_excel(writer, sheet_name='Importancia_Variaveis')

    print(f" ✅ Relatório de ML gerado: data/{arquivo_excel.name}")
    print(" 🔎 Verifique a aba 'Comparativo_Modelos' para ver o campeão.")

except Exception as e:
    print(f" ❌ Erro ao salvar: {e}")