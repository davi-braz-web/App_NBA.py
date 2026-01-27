# ============================================================
# limpeza_nba_dados.py
# ------------------------------------------------------------
# Limpeza básica da base da NBA coletada via API
# Mantém as duas versões dos jogos (mandante e visitante)
# Gera um novo arquivo CSV limpo e organizado
# ============================================================

import pandas as pd

# === 1. LER O ARQUIVO GERADO PELA COLETA ===
arquivo_entrada = "data/nba_games_2022_2026.csv"
df = pd.read_csv(arquivo_entrada)

print(f"✅ Arquivo carregado com {len(df):,} linhas e {len(df.columns)} colunas.")

# === 2. TRATAMENTO DE DADOS ===

# Converter datas
df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'], errors='coerce')

# Remover linhas com dados ausentes em colunas essenciais
df = df.dropna(subset=['PTS', 'REB', 'AST', 'WL'])

# Garantir que colunas numéricas estejam no formato certo
cols_numericas = ['PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV',
                  'FG_PCT', 'FT_PCT', 'FG3_PCT', 'PLUS_MINUS']
for c in cols_numericas:
    df[c] = pd.to_numeric(df[c], errors='coerce')

# Criar variável binária de vitória (1 = vitória, 0 = derrota)
df['WIN'] = df['WL'].apply(lambda x: 1 if x == 'W' else 0)

# === 3. REORDENAR COLUNAS PARA ORGANIZAR MELHOR ===
colunas_ordenadas = [
    'GAME_ID', 'GAME_DATE', 'TEAM_NAME', 'MATCHUP', 'WL', 'WIN',
    'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV',
    'FG_PCT', 'FT_PCT', 'FG3_PCT', 'PLUS_MINUS', 'SEASON_ID'
]
df = df[colunas_ordenadas]

# === 4. SALVAR ARQUIVO LIMPO ===
arquivo_saida = "data/nba_dados_limpos.csv"
df.to_csv(arquivo_saida, index=False)

print(f"✅ Base limpa salva como: {arquivo_saida}")
print(f"Total de registros finais: {len(df):,}")

# === 5. MOSTRAR AMOSTRA ===
print("\nPrévia dos dados limpos:")
print(df.head(10))

# === 6. GERAR TABELA BAIXÁVEL ===
arquivo_excel = "data/nba_dados_limpos.xlsx"
df.to_excel(arquivo_excel, index=False)
print(f"📊 Versão Excel salva como: {arquivo_excel}")
