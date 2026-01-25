import pandas as pd
import numpy as np
import statsmodels.api as sm
from pathlib import Path
from sklearn.metrics import accuracy_score, roc_auc_score

# ============================================================
# ETAPA 1 — PREPARAÇÃO SEGURA DA BASE
# ============================================================
print(" 🚀 Iniciando Modelagem Avançada (Versão Final)")

arquivo_features = "data/base_com_features_ENRICHED.csv"

# 1. Carregamento
try:
    df = pd.read_csv(arquivo_features)
except FileNotFoundError:
    raise FileNotFoundError(f"❌ ERRO: O arquivo '{arquivo_features}' não existe. Rode o script de 'feature_engineering' primeiro.")

# 2. Tratamento de Dados
df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'], errors='coerce')
df['YEAR'] = df['GAME_DATE'].dt.year
df['VITORIA'] = pd.to_numeric(df['VITORIA'], errors='coerce')

# 3. Definição de Variáveis (Diferenciais e Contexto)
vars_desejadas = [
    'IS_HOME', 'IS_B2B', 
    'PTS_DIFF', 'REB_DIFF', 'AST_DIFF', 'STL_DIFF', 'BLK_DIFF', 'TOV_DIFF',
    'FG_PCT_DIFF', 'FT_PCT_DIFF', 'FG3_PCT_DIFF'
]

# 4. Verificação: Usa apenas as colunas que realmente existem
vars_modelo = [col for col in vars_desejadas if col in df.columns]

if not vars_modelo:
    print(" ❌ ERRO CRÍTICO: Nenhuma variável de modelo encontrada na base.")
    print(f"    Colunas disponíveis: {list(df.columns)}")
    exit()

# 5. Limpeza Profunda (NaNs e Infinitos)
colunas_finais = ['VITORIA', 'YEAR'] + vars_modelo
df_modelo = df[colunas_finais].copy()

# Substitui infinitos por NaN e remove linhas nulas
df_modelo.replace([np.inf, -np.inf], np.nan, inplace=True)
df_modelo.dropna(inplace=True)

print(f" ✅ Base pronta: {len(df_modelo)} jogos | {len(vars_modelo)} variáveis preditoras.")

# ============================================================
# ETAPA 2 — CENÁRIOS DE VALIDAÇÃO
# ============================================================
scenarios = {
    "Cenario_A (Treino_22_23, Teste_24)": {'Train_Years': [2022, 2023], 'Test_Years': [2024]},
    "Cenario_B (Treino_23_24, Teste_25)": {'Train_Years': [2023, 2024], 'Test_Years': [2025]},
    "Cenario_C (Treino_22_23_24, Teste_25)": {'Train_Years': [2022, 2023, 2024], 'Test_Years': [2025]},
    "Cenario_Geral (Robustez)": {'Train_Years': [2022, 2023, 2024, 2025], 'Test_Years': [2022, 2023, 2024, 2025]}
}

resultados_coefs = {}
resultados_odds = {}
resultados_metricas = {}

# ============================================================
# ETAPA 3 — LOOP DE MODELAGEM
# ============================================================
for scenario_name, years in scenarios.items():
    print(f"\n ⚙️  Processando: {scenario_name}...")
    
    # Filtros
    mask_train = df_modelo['YEAR'].isin(years['Train_Years'])
    mask_test = df_modelo['YEAR'].isin(years['Test_Years'])

    X_treino = df_modelo.loc[mask_train, vars_modelo]
    Y_treino = df_modelo.loc[mask_train, 'VITORIA']
    X_teste = df_modelo.loc[mask_test, vars_modelo]
    Y_teste = df_modelo.loc[mask_test, 'VITORIA']

    if len(X_treino) < 10 or len(X_teste) < 10:
        print(f"    ⚠️ Pular: Dados insuficientes.")
        continue

    # Ajuste (Logit)
    X_treino_sm = sm.add_constant(X_treino)
    X_teste_sm = sm.add_constant(X_teste)

    try:
        modelo = sm.Logit(Y_treino, X_treino_sm).fit(disp=False)
        
        # Predição
        probs = modelo.predict(X_teste_sm)
        preds = (probs >= 0.5).astype(int)
        
        # Métricas
        acc = accuracy_score(Y_teste, preds)
        auc = roc_auc_score(Y_teste, probs)
        print(f"    -> Acurácia: {acc:.4f} | AUC: {auc:.4f}")

        # Armazenar Resultados
        resultados_metricas[scenario_name] = pd.DataFrame({
            'Métrica': ['Acurácia', 'AUC', 'Amostras'], 'Valor': [acc, auc, len(Y_teste)]
        }).set_index('Métrica')

        resultados_odds[scenario_name] = pd.DataFrame({
            'Odds Ratio': np.exp(modelo.params), 'P-Value': modelo.pvalues
        }).round(4)

        resultados_coefs[scenario_name] = pd.DataFrame({
            'Coef': modelo.params, 'P>|z|': modelo.pvalues, 'StdErr': modelo.bse
        }).round(4)

    except Exception as e:
        print(f"    ❌ Erro no cálculo: {e}")
        continue

# ============================================================
# ETAPA 4 — EXPORTAÇÃO (CORRIGIDA)
# ============================================================
print("\n 💾 Exportando Relatório Final...")

# 1. Define o caminho ANTES de tentar salvar
out_dir = Path(".")
out_dir.mkdir(parents=True, exist_ok=True)
arquivo_excel_saida = out_dir / "data/relatorio_modelo_avancado_v2.xlsx"

# 2. Verifica se existem resultados para salvar
if not resultados_metricas:
    print(" ❌ ERRO: Nenhum resultado foi gerado. Verifique se os dados estão corretos.")
else:
    try:
        with pd.ExcelWriter(arquivo_excel_saida, engine='openpyxl') as writer:
            # Salva métricas
            pd.concat(resultados_metricas, axis=1).to_excel(writer, sheet_name='METRICAS_FINAIS')
            # Salva Odds Ratios
            pd.concat(resultados_odds, axis=1).to_excel(writer, sheet_name='ODDS_RATIOS')
            # Salva Detalhes
            for nome, df_res in resultados_coefs.items():
                safe_name = nome.split('(')[0].strip().replace(' ', '_')[:30]
                df_res.to_excel(writer, sheet_name=f"Det_{safe_name}")
                
        print(f" ✅ SUCESSO! Relatório salvo em: {arquivo_excel_saida.resolve()}")
        print(" 🔎 Abra o Excel e compare a aba 'METRICAS_FINAIS' com seus resultados anteriores.")
        
    except PermissionError:
        print(f" ❌ ERRO DE PERMISSÃO: O arquivo '{arquivo_excel_saida.name}' está aberto no Excel?")
        print("    Feche o arquivo Excel e tente rodar novamente.")
    except Exception as e:
        print(f" ❌ Erro desconhecido na exportação: {e}")