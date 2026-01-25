import pandas as pd
import numpy as np
from nba_api.stats.endpoints import leaguegamefinder
from nba_api.stats.static import teams
import time
import sys

print(" 🏗️  A INICIAR RECONSTRUÇÃO TOTAL DA BASE DE DADOS...")
print("     Isto pode demorar alguns minutos, pois vamos baixar 4 anos de NBA.")

# ============================================================
# 1. COLETA DE DADOS (2022 a 2025)
# ============================================================
# Formato da API da NBA: 2 + Ano (Ex: 2022 -> 22022)
anos_coleta = ['22022', '22023', '22024', '22025'] 
print(f" 📅 Temporadas alvo: {anos_coleta}")

nba_teams = teams.get_teams()
tabelas = []

print(f" ⏳ A coletar dados de {len(nba_teams)} equipas...")

for i, team in enumerate(nba_teams):
    print(f"    [{i+1}/{len(nba_teams)}] A baixar: {team['full_name']}...")
    try:
        # Pausa para evitar bloqueio da API
        time.sleep(0.6)
        
        # Busca TODOS os jogos da equipa
        # Ao buscar por TeamID, a API traz a visão DESSA equipa no jogo.
        # Fazendo isso para os 30 times, garantimos as 2 linhas por jogo automaticamente.
        gamefinder = leaguegamefinder.LeagueGameFinder(
            team_id_nullable=team['id'],
            league_id_nullable='00' # Apenas NBA Principal (Ignora G-League/Pre-Season)
        )
        df_time = gamefinder.get_data_frames()[0]
        
        # Filtra apenas as temporadas que queremos
        df_time = df_time[df_time['SEASON_ID'].isin(anos_coleta)].copy()
        
        if not df_time.empty:
            df_time['TEAM_NAME'] = team['full_name'] # Garante nome correto e padronizado
            tabelas.append(df_time)
            
    except Exception as e:
        print(f"    ⚠️ Erro ao baixar {team['full_name']}: {e}")

if not tabelas:
    print(" ❌ Erro Crítico: Nenhum dado foi baixado. Verifique a sua conexão.")
    sys.exit()

# Consolida
df_raw = pd.concat(tabelas, ignore_index=True)
print(f" ✅ Coleta concluída. Total de registos brutos: {len(df_raw)}")

# ============================================================
# 2. LIMPEZA E PADRONIZAÇÃO
# ============================================================
print(" 🧹 A limpar dados...")

# Remove duplicatas exatas, mas mantém jogos onde o TEAM_NAME é diferente
# (Ex: Lakers vs Celtics e Celtics vs Lakers são mantidos, pois são perspectivas diferentes)
df_raw = df_raw.drop_duplicates(subset=['GAME_ID', 'TEAM_NAME'])

# Seleção de colunas
cols_necessarias = [
    'GAME_ID', 'GAME_DATE', 'TEAM_NAME', 'MATCHUP', 'WL',
    'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV',
    'FG_PCT', 'FT_PCT', 'FG3_PCT'
]
df = df_raw[cols_necessarias].copy()

# Tratamento de Tipos
df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'])
df['VITORIA'] = df['WL'].apply(lambda x: 1 if x == 'W' else 0)

for col in ['PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'FG_PCT', 'FT_PCT', 'FG3_PCT']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Ordenação (CRUCIAL para o cálculo de médias móveis)
df = df.sort_values(['TEAM_NAME', 'GAME_DATE']).reset_index(drop=True)

# ============================================================
# 3. FEATURE ENGINEERING 1: MÉDIAS PONDERADAS (Recência)
# ============================================================
print(" 🧠 A calcular médias móveis (Weighted Recency)...")

vars_stats = ['PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'FG_PCT', 'FT_PCT', 'FG3_PCT']

# Média Móvel Exponencial (Dá mais peso aos últimos 10 jogos)
# Shift(1) é OBRIGATÓRIO para não usar dados do próprio jogo na previsão (Data Leakage)
df_medias = df.copy()
for col in vars_stats:
    df_medias[f'{col}_MEAN'] = df_medias.groupby('TEAM_NAME')[col]\
        .transform(lambda x: x.ewm(span=10, adjust=False).mean().shift(1))

# Remove as primeiras linhas de cada equipa (que ficam NaN por não ter histórico anterior)
df_medias.dropna(subset=[f'{c}_MEAN' for c in vars_stats], inplace=True)

# Salva a base de médias (usada pelo App para pegar status atual)
df_medias.to_csv("data/base_com_features_FINAL.csv", index=False)
print(f"    -> 'data/base_com_features_FINAL.csv' salvo com {len(df_medias)} linhas.")

# ============================================================
# 4. FEATURE ENGINEERING 2: DIFERENCIAIS E CONTEXTO
# ============================================================
print(" ⚔️  A criar base enriquecida (Diferenciais)...")

# Contexto
df_medias['IS_HOME'] = df_medias['MATCHUP'].apply(lambda x: 1 if 'vs.' in str(x) else 0)
df_medias['DAYS_REST'] = df_medias.groupby('TEAM_NAME')['GAME_DATE'].diff().dt.days.fillna(3)
df_medias['IS_B2B'] = (df_medias['DAYS_REST'] == 1).astype(int)

# Diferenciais (Equipa - Oponente)
# Precisamos juntar o jogo da Equipa A com o jogo da Equipa B
cols_mean = [f'{c}_MEAN' for c in vars_stats]
df_stats_only = df_medias[['GAME_ID', 'TEAM_NAME'] + cols_mean]

# Self-Merge pelo ID do Jogo
# Isso cria uma linha com Stats_Time_A e Stats_Time_B lado a lado
df_merged = pd.merge(df_medias, df_stats_only, on='GAME_ID', suffixes=('', '_OPP'))

# Filtra para ter a linha onde o Oponente é diferente do Time Principal
df_enriched = df_merged[df_merged['TEAM_NAME'] != df_merged['TEAM_NAME_OPP']].copy()

# Calcula a subtração
for col in cols_mean:
    new_col = col.replace('_MEAN', '_DIFF')
    df_enriched[new_col] = df_enriched[col] - df_enriched[f'{col}_OPP']

# Limpeza Final
cols_drop = [c for c in df_enriched.columns if '_OPP' in c]
df_enriched.drop(columns=cols_drop, inplace=True)

# Removemos duplicatas de jogo/time para garantir integridade
df_enriched = df_enriched.drop_duplicates(subset=['GAME_ID', 'TEAM_NAME'])

# Salva a base final de treino
df_enriched.to_csv("data/base_com_features_ENRICHED.csv", index=False)

print(f" ✅ RECONSTRUÇÃO TOTAL CONCLUÍDA!")
print(f"    Base Enriquecida Final: {len(df_enriched)} linhas (Esperado: > 6000).")
print("\n ⚠️  IMPORTANTE: Agora execute o 'deploy_modelo_final.py' para treinar a IA com esta nova base completa.")