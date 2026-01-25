import pandas as pd
import numpy as np
import statsmodels.api as sm
import joblib
import sys
import os

print("\n🚀 Iniciando Deploy do Sistema NBA (Correção TEAM_NAME)...\n")

# ============================================================
# 1. CARREGAR DADOS DE TREINO
# ============================================================
arquivo_treino = "data/base_com_features_ENRICHED.csv"

if not os.path.exists(arquivo_treino):
    print(f"❌ ERRO: Arquivo '{arquivo_treino}' não encontrado!")
    sys.exit()

df = pd.read_csv(arquivo_treino)

# Padronizar nomes de colunas
df.columns = df.columns.str.strip().str.upper()

print(f"✅ Arquivo de treino carregado. Colunas encontradas: {list(df.columns)}")

# Tratamento básico
if 'GAME_DATE' in df.columns:
    df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'], errors='coerce')

# Verifica coluna alvo
if 'VITORIA' not in df.columns:
    if 'WIN' in df.columns: df.rename(columns={'WIN': 'VITORIA'}, inplace=True)
    elif 'WL' in df.columns: 
        df['VITORIA'] = df['WL'].apply(lambda x: 1 if x == 'W' else 0)
    else:
        print("❌ ERRO: Coluna de vitória (VITORIA/WIN) não encontrada.")
        sys.exit()

df['VITORIA'] = pd.to_numeric(df['VITORIA'], errors='coerce')

# ============================================================
# 2. TREINAR MODELO
# ============================================================
print("🧠 Treinando modelo...")

vars_modelo = [
    'IS_HOME', 'IS_B2B', 
    'PTS_DIFF', 'REB_DIFF', 'AST_DIFF',
    'STL_DIFF', 'BLK_DIFF', 'TOV_DIFF',
    'FG_PCT_DIFF', 'FT_PCT_DIFF', 'FG3_PCT_DIFF'
]

vars_finais = [c for c in vars_modelo if c in df.columns]

if not vars_finais:
    print("❌ ERRO: Nenhuma variável de modelo encontrada no arquivo.")
    sys.exit()

df_modelo = df[['VITORIA'] + vars_finais].copy()
df_modelo.replace([np.inf, -np.inf], np.nan, inplace=True)
df_modelo.dropna(inplace=True)

X = sm.add_constant(df_modelo[vars_finais])
y = df_modelo['VITORIA']

try:
    modelo = sm.Logit(y, X).fit(disp=False)
    print("✅ Modelo treinado com sucesso.")
except Exception as e:
    print(f"❌ ERRO ao treinar modelo: {e}")
    sys.exit()

# ============================================================
# 3. CAPTURAR ESTATÍSTICAS ATUAIS (CORREÇÃO APLICADA)
# ============================================================
print("📸 Capturando estatísticas atuais...")

arquivo_stats = "data/base_com_features_FINAL.csv"
if not os.path.exists(arquivo_stats):
    print(f"⚠️ Aviso: '{arquivo_stats}' não encontrado. Tentando usar '{arquivo_treino}'.")
    arquivo_stats = arquivo_treino 

df_stats = pd.read_csv(arquivo_stats)
df_stats.columns = df_stats.columns.str.strip().str.upper()

# Identifica nome correto da coluna de time
coluna_time = None
possiveis_nomes = ['TEAM_NAME', 'TEAM', 'TIME', 'EQUIPE', 'NOMEDOTIME']

for c in possiveis_nomes:
    if c in df_stats.columns:
        coluna_time = c
        break

if coluna_time is None:
    print("❌ ERRO CRÍTICO: Não foi possível encontrar a coluna com o nome do time.")
    sys.exit()

print(f"   -> Usando coluna '{coluna_time}' como identificador.")

# Identifica colunas de média
cols_mean = [c for c in df_stats.columns if '_MEAN' in c]

if not cols_mean:
    print("❌ ERRO: Nenhuma coluna de média (_MEAN) encontrada.")
    sys.exit()

# --- CORREÇÃO AQUI: Incluir 'coluna_time' na seleção ---
# Precisamos garantir que o nome do time esteja na lista de colunas a serem preservadas
cols_to_keep = cols_mean + [coluna_time]

# Garante data
if 'GAME_DATE' in df_stats.columns:
    df_stats['GAME_DATE'] = pd.to_datetime(df_stats['GAME_DATE'], errors='coerce')
    # Ordena e pega o último (mantendo a coluna do time)
    stats_atuais = df_stats.sort_values('GAME_DATE').groupby(coluna_time)[cols_to_keep].tail(1)
else:
    stats_atuais = df_stats.groupby(coluna_time)[cols_to_keep].tail(1)

# Agora sim podemos setar o index, pois a coluna existe
stats_atuais = stats_atuais.set_index(coluna_time)

print(f"✅ Estatísticas carregadas para {len(stats_atuais)} times.")

# ============================================================
# 4. SALVAR SISTEMA
# ============================================================
pacote = {
    "modelo": modelo,
    "variaveis": vars_finais,
    "stats_atuais": stats_atuais
}

joblib.dump(pacote, "data/sistema_nba_v1.pkl")
print("\n✅ SUCESSO TOTAL! 'data/sistema_nba_v1.pkl' gerado.")
print("   Agora pode rodar: streamlit run app_nba.py")
