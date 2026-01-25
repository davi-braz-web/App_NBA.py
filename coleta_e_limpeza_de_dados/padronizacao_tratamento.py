# ============================================================
# padronizacao_tratamento.py
# ------------------------------------------------------------
# Etapa de padronização de nomes e tratamento de valores ausentes
# Gera uma base final consolidada e padronizada
# ============================================================

import pandas as pd
import numpy as np

# === 1. LER O ARQUIVO LIMPO GERADO NA ETAPA ANTERIOR ===
df = pd.read_csv("data/nba_dados_limpos.csv")
print(f"✅ Base carregada com {len(df):,} linhas e {len(df.columns)} colunas.")

# === 2. PADRONIZAÇÃO DE NOMES DE TIMES ===
# Cria um dicionário com nomes padronizados
padroniza_times = {
    "LA Clippers": "Los Angeles Clippers",
    "LA Lakers": "Los Angeles Lakers",
    "Portland Trailblazers": "Portland Trail Blazers",
    "Golden St. Warriors": "Golden State Warriors",
    "NY Knicks": "New York Knicks",
    "N.Y. Knicks": "New York Knicks",
    "SAS": "San Antonio Spurs",
    "GSW": "Golden State Warriors",
    "BKN": "Brooklyn Nets",
    "PHX": "Phoenix Suns"
}

# Aplica a padronização
df['TEAM_NAME'] = df['TEAM_NAME'].replace(padroniza_times)

# Remove espaços extras e transforma tudo em maiúsculas (padronização total)
df['TEAM_NAME'] = df['TEAM_NAME'].str.strip().str.upper()

print("🔠 Nomes de times padronizados com sucesso.")
print(f"Total de times únicos: {df['TEAM_NAME'].nunique()}")

# === 3. TRATAMENTO DE VALORES AUSENTES (MISSING VALUES) ===

# Verificar a quantidade de valores ausentes
print("\n📋 Valores ausentes por coluna:")
print(df.isna().sum())

# Estratégias de tratamento:
# - Preencher médias para colunas numéricas (não queremos perder dados)
# - Remover registros se tiverem informações críticas ausentes (como TEAM_NAME ou GAME_DATE)

# Preencher valores numéricos ausentes com a média da coluna
colunas_numericas = ['PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV',
                     'FG_PCT', 'FT_PCT', 'FG3_PCT', 'PLUS_MINUS']
for col in colunas_numericas:
    media_coluna = df[col].mean()
    df[col] = df[col].fillna(media_coluna)

# Remover linhas sem nome de time ou data de jogo
df = df.dropna(subset=['TEAM_NAME', 'GAME_DATE'])

# === 4. CHECAGEM FINAL DE CONSISTÊNCIA ===
print("\n✅ Após tratamento, valores ausentes restantes:")
print(df.isna().sum())

# === 5. SALVAR BASE FINAL ===
arquivo_saida = "data/nba_dados_padronizados.csv"
df.to_csv(arquivo_saida, index=False)
print(f"\n💾 Base final salva como: {arquivo_saida}")
print(f"Total de registros: {len(df):,}")

# === 6. PRÉVIA DO RESULTADO ===
print("\n📊 Amostra da base final:")
print(df.head(10))

# === 7. GERAR ARQUIVO EXCEL ===
arquivo_excel = "data/nba_dados_padronizados.xlsx"
df.to_excel(arquivo_excel, index=False)
print(f"📊 Versão Excel salva como: {arquivo_excel}")
