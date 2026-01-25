import pandas as pd
import numpy as np
import joblib
import os
import sys
import json
from datetime import datetime
from nba_api.stats.endpoints import scoreboardv2
from nba_api.stats.static import teams

print("🤖 INICIANDO ROBÔ DE PREVISÃO DIÁRIA...\n")

# ============================================================
# 1. CARREGAR O CÉREBRO (MODELO)
# ============================================================
nome_arquivo_modelo = "data/sistema_nba_v1.pkl"

if not os.path.exists(nome_arquivo_modelo):
    print(f"❌ ERRO: '{nome_arquivo_modelo}' não encontrado.")
    sys.exit()

sistema = joblib.load(nome_arquivo_modelo)
modelo = sistema["modelo"]
stats = sistema["stats_atuais"]
features = sistema["variaveis"]

print("✅ Modelo carregado.")

# === CORREÇÃO DE NOMES (O "TRADUTOR") ===
mapa_nomes = {nome.upper(): nome for nome in stats.index}
print(f"📚 Base de conhecimento: {len(mapa_nomes)} times mapeados.")

# ============================================================
# 2. BUSCAR JOGOS DE HOJE (API)
# ============================================================
print("📅 Consultando a agenda da NBA...")

hoje = datetime.now()
# hoje = datetime(2025, 12, 16) # Para testes manuais

try:
    board = scoreboardv2.ScoreboardV2(game_date=hoje.strftime('%Y-%m-%d'))
    jogos = board.game_header.get_data_frame()
    
    if jogos.empty:
        print("⚠️ Nenhum jogo agendado para hoje.")
        sys.exit()
        
    print(f"🏀 Jogos encontrados (bruto): {len(jogos)}")

except Exception as e:
    print(f"❌ Erro na API: {e}")
    sys.exit()

# Mapeamento IDs da API -> Nomes
nba_teams = teams.get_teams()
id_to_name_api = {int(t['id']): t['full_name'] for t in nba_teams}

# ============================================================
# 3. CARREGAR HISTÓRICO E PREPARAR
# ============================================================
ARQUIVO_HISTORICO = "data/historico_previsoes.json"
os.makedirs("data", exist_ok=True)

lista_historico = []
ids_existentes = set()

if os.path.exists(ARQUIVO_HISTORICO):
    try:
        with open(ARQUIVO_HISTORICO, 'r') as f:
            lista_historico = json.load(f)
            # Cria um set com os IDs que já estão no histórico para não duplicar
            ids_existentes = {item.get('GAME_ID') for item in lista_historico if 'GAME_ID' in item}
    except Exception as e:
        print(f"⚠️ Erro ao ler histórico: {e}. Criando novo.")

print("\n🔮 Calculando probabilidades...")

novas_previsoes = []
jogos_processados_hoje = set() # Controle local para a execução atual

for _, jogo in jogos.iterrows():
    try:
        # === CORREÇÃO DE DUPLICIDADE ===
        game_id = str(jogo['GAME_ID']) # Converter para string para padronizar JSON
        
        # Se já processou hoje ou já está no histórico, pula
        if game_id in jogos_processados_hoje or game_id in ids_existentes:
            continue
            
        jogos_processados_hoje.add(game_id)

        # === CORREÇÃO CRÍTICA ===
        # Verifica se os IDs são nulos (None/NaN) antes de converter
        if pd.isna(jogo['HOME_TEAM_ID']) or pd.isna(jogo['VISITOR_TEAM_ID']):
            continue

        id_casa = int(jogo['HOME_TEAM_ID'])
        id_vis = int(jogo['VISITOR_TEAM_ID'])
        
        # Pega nomes usando o ID
        nome_casa_api = id_to_name_api.get(id_casa, "Unknown")
        nome_vis_api = id_to_name_api.get(id_vis, "Unknown")
        
        # Tenta encontrar o nome correspondente na NOSSA base
        time_casa = mapa_nomes.get(nome_casa_api.upper())
        time_fora = mapa_nomes.get(nome_vis_api.upper())
        
        # Fallback para Clippers
        if not time_casa and "CLIPPERS" in nome_casa_api.upper():
            time_casa = mapa_nomes.get("L.A. CLIPPERS") or mapa_nomes.get("LOS ANGELES CLIPPERS")
        if not time_fora and "CLIPPERS" in nome_vis_api.upper():
            time_fora = mapa_nomes.get("L.A. CLIPPERS") or mapa_nomes.get("LOS ANGELES CLIPPERS")

        # Verifica se achou os times
        if not time_casa or not time_fora:
            if nome_casa_api != "Unknown":
                print(f"   ⚠️ Pulei: {nome_casa_api} vs {nome_vis_api} - Nome não bateu com a base")
            continue
            
        print(f"   -> Analisando: {time_casa} vs {time_fora}...", end=" ")

        # Recupera Stats
        s_casa = stats.loc[time_casa]
        s_fora = stats.loc[time_fora]
        
        if isinstance(s_casa, pd.DataFrame): s_casa = s_casa.iloc[0]
        if isinstance(s_fora, pd.DataFrame): s_fora = s_fora.iloc[0]

        # Monta Input
        input_data = {'const': 1.0, 'IS_HOME': 1, 'IS_B2B': 0}
        
        for col in features:
            if '_DIFF' in col:
                base = col.replace('_DIFF', '_MEAN')
                val_c = s_casa.get(base, 0)
                val_f = s_fora.get(base, 0)
                input_data[col] = val_c - val_f
        
        # Previsão
        df_input = pd.DataFrame([input_data])
        for col in ['const'] + features:
            if col not in df_input.columns: df_input[col] = 0.0
            
        cols_modelo = ['const'] + features
        prob_casa = modelo.predict(df_input[cols_modelo])[0]
        
        # Resultado
        favorito = time_casa if prob_casa > 0.5 else time_fora
        prob_venc = prob_casa if prob_casa > 0.5 else 1 - prob_casa
        
        print(f"✅ Favorito: {favorito} ({prob_venc*100:.1f}%)")
        
        # Adiciona à lista de novas previsões
        novas_previsoes.append({
            'DATA': hoje.strftime('%Y-%m-%d'),
            'GAME_ID': game_id,
            'CASA': time_casa,
            'VISITANTE': time_fora,
            'PROB_CASA': float(prob_casa), # float nativo para JSON
            'ODD_JUSTA_CASA': float(1/prob_casa if prob_casa > 0 else 99),
            'ODD_JUSTA_VIS': float(1/(1-prob_casa) if prob_casa < 1 else 99),
            'VENCEDOR': favorito,
            'CONFIANCA': 'ALTA' if prob_venc > 0.65 else 'MÉDIA' if prob_venc > 0.55 else 'BAIXA'
        })

    except Exception as e:
        print(f" [ERRO JOGO: {e}]")

# ============================================================
# 4. SALVAR NO ARQUIVO JSON
# ============================================================
if novas_previsoes:
    # Adiciona as novas ao histórico
    lista_historico.extend(novas_previsoes)
    
    # Salva o arquivo completo
    with open(ARQUIVO_HISTORICO, 'w') as f:
        json.dump(lista_historico, f, indent=4)
        
    print(f"\n📄 Base atualizada: {ARQUIVO_HISTORICO}")
    print(f"✅ {len(novas_previsoes)} novos jogos adicionados.")
    
    # Mostra preview
    df_preview = pd.DataFrame(novas_previsoes)
    print(df_preview[['CASA', 'VISITANTE', 'VENCEDOR', 'CONFIANCA']].to_string(index=False))
else:
    print("\n⚠️ Nenhuma previsão NOVA gerada hoje (jogos já estavam no histórico ou filtrados).")