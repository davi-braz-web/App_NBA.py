# ============================================================
# coleta_nba_estavel_v2.py
# ------------------------------------------------------------
# Coleta estável e compatível com versões atuais da nba_api
# ------------------------------------------------------------

from nba_api.stats.endpoints import leaguegamefinder
from nba_api.stats.static import teams
import pandas as pd
import time
from datetime import datetime
import requests
import os  # Adicionado para gerenciamento de pastas

# === 1. PARÂMETROS ===
ANO_INICIO = 2022
ANO_ATUAL = datetime.now().year
TEMPORADAS = [f"2{ano}" for ano in range(ANO_INICIO, ANO_ATUAL + 1)]
print(f"Coletando temporadas: {TEMPORADAS}")

# === 2. CONFIGURAÇÃO GLOBAL DO USER-AGENT ===
# Corrige bloqueios por parte da API da NBA
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Referer': 'https://www.nba.com/',
    'Origin': 'https://www.nba.com'
})

# Substitui a sessão interna da nba_api por esta
import nba_api.library.http as nba_http
nba_http._SESSION = session

# === 3. LISTA DE TIMES ===
nba_teams = teams.get_teams()
print(f"Total de times: {len(nba_teams)}")

# === 4. FUNÇÃO DE COLETA ===
def coletar_jogos_por_time(team_id, max_tentativas=3):
    for tentativa in range(1, max_tentativas + 1):
        try:
            gamefinder = leaguegamefinder.LeagueGameFinder(team_id_nullable=team_id)
            df = gamefinder.get_data_frames()[0]
            df = df[df['SEASON_ID'].isin(TEMPORADAS)]
            return df
        except Exception as e:
            print(f"⚠️ Tentativa {tentativa} falhou: {e}")
            time.sleep(10 * tentativa)
    return pd.DataFrame()

# === 5. LOOP EM TODOS OS TIMES ===
tabelas = []
for t in nba_teams:
    nome = t['full_name']
    team_id = t['id']
    print(f"\n⏳ Coletando jogos de: {nome}")
    df_time = coletar_jogos_por_time(team_id)
    if not df_time.empty:
        df_time['TEAM_NAME'] = nome
        tabelas.append(df_time)
        print(f"✅ {len(df_time)} jogos coletados.")
    else:
        print(f"⚠️ Nenhum dado retornado para {nome}.")
    time.sleep(5)

# === 6. CONSOLIDAR ===
if tabelas:
    df_total = pd.concat(tabelas, ignore_index=True)
    colunas = [
        'GAME_ID', 'GAME_DATE', 'SEASON_ID', 'MATCHUP', 'WL',
        'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV',
        'FG_PCT', 'FT_PCT', 'FG3_PCT', 'PLUS_MINUS', 'TEAM_NAME'
    ]
    df_total = df_total[colunas]
    df_total['GAME_DATE'] = pd.to_datetime(df_total['GAME_DATE'])
    df_total = df_total.sort_values('GAME_DATE')

    # --- AJUSTE: Criação automática da pasta data ---
    if not os.path.exists("data"):
        os.makedirs("data")
        print("📁 Pasta 'data' criada com sucesso.")

    arquivo_saida = f"data/nba_games_{ANO_INICIO}_{ANO_ATUAL}.csv"
    df_total.to_csv(arquivo_saida, index=False)
    print(f"\n✅ Base consolidada salva em: {arquivo_saida}")
    print(f"Total de jogos coletados: {len(df_total):,}")
else:
    print("❌ Nenhum dado coletado.")