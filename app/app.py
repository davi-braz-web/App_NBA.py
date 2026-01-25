import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os
import json
from datetime import datetime

# --- TENTA IMPORTAR A ENGINE IA ---
try:
    from funcionalidades_do_app.matchups_ia import XAIEngineNBA
except ImportError:
    XAIEngineNBA = None
# ----------------------------------

# === CONFIGURAÇÃO VISUAL ===
st.set_page_config(page_title="NBA Sniper Pro", page_icon="🏀", layout="wide")

# Mapeamento de Logos
NBA_LOGOS = {
    'ATLANTA HAWKS': 'https://cdn.nba.com/logos/nba/1610612737/global/L/logo.svg',
    'BOSTON CELTICS': 'https://cdn.nba.com/logos/nba/1610612738/global/L/logo.svg',
    'BROOKLYN NETS': 'https://cdn.nba.com/logos/nba/1610612751/global/L/logo.svg',
    'CHARLOTTE HORNETS': 'https://cdn.nba.com/logos/nba/1610612766/global/L/logo.svg',
    'CHICAGO BULLS': 'https://cdn.nba.com/logos/nba/1610612741/global/L/logo.svg',
    'CLEVELAND CAVALIERS': 'https://cdn.nba.com/logos/nba/1610612739/global/L/logo.svg',
    'DALLAS MAVERICKS': 'https://cdn.nba.com/logos/nba/1610612742/global/L/logo.svg',
    'DENVER NUGGETS': 'https://cdn.nba.com/logos/nba/1610612743/global/L/logo.svg',
    'DETROIT PISTONS': 'https://cdn.nba.com/logos/nba/1610612765/global/L/logo.svg',
    'GOLDEN STATE WARRIORS': 'https://cdn.nba.com/logos/nba/1610612744/global/L/logo.svg',
    'HOUSTON ROCKETS': 'https://cdn.nba.com/logos/nba/1610612745/global/L/logo.svg',
    'INDIANA PACERS': 'https://cdn.nba.com/logos/nba/1610612754/global/L/logo.svg',
    'LOS ANGELES CLIPPERS': 'https://cdn.nba.com/logos/nba/1610612746/global/L/logo.svg',
    'LOS ANGELES LAKERS': 'https://cdn.nba.com/logos/nba/1610612747/global/L/logo.svg',
    'MEMPHIS GRIZZLIES': 'https://cdn.nba.com/logos/nba/1610612763/global/L/logo.svg',
    'MIAMI HEAT': 'https://cdn.nba.com/logos/nba/1610612748/global/L/logo.svg',
    'MILWAUKEE BUCKS': 'https://cdn.nba.com/logos/nba/1610612749/global/L/logo.svg',
    'MINNESOTA TIMBERWOLVES': 'https://cdn.nba.com/logos/nba/1610612750/global/L/logo.svg',
    'NEW ORLEANS PELICANS': 'https://cdn.nba.com/logos/nba/1610612740/global/L/logo.svg',
    'NEW YORK KNICKS': 'https://cdn.nba.com/logos/nba/1610612752/global/L/logo.svg',
    'OKLAHOMA CITY THUNDER': 'https://cdn.nba.com/logos/nba/1610612760/global/L/logo.svg',
    'ORLANDO MAGIC': 'https://cdn.nba.com/logos/nba/1610612753/global/L/logo.svg',
    'PHILADELPHIA 76ERS': 'https://cdn.nba.com/logos/nba/1610612755/global/L/logo.svg',
    'PHOENIX SUNS': 'https://cdn.nba.com/logos/nba/1610612756/global/L/logo.svg',
    'PORTLAND TRAIL BLAZERS': 'https://cdn.nba.com/logos/nba/1610612757/global/L/logo.svg',
    'SACRAMENTO KINGS': 'https://cdn.nba.com/logos/nba/1610612758/global/L/logo.svg',
    'SAN ANTONIO SPURS': 'https://cdn.nba.com/logos/nba/1610612759/global/L/logo.svg',
    'TORONTO RAPTORS': 'https://cdn.nba.com/logos/nba/1610612761/global/L/logo.svg',
    'UTAH JAZZ': 'https://cdn.nba.com/logos/nba/1610612762/global/L/logo.svg',
    'WASHINGTON WIZARDS': 'https://cdn.nba.com/logos/nba/1610612764/global/L/logo.svg'
}
DEFAULT_LOGO = "https://cdn.nba.com/logos/leagues/logo-nba.svg"

# CSS Profissional Atualizado
st.markdown("""
    <style>
    .big-font { font-size: 24px !important; font-weight: bold; }
    .vs-text { font-size: 40px; font-weight: 900; color: #ef4444; text-align: center; padding-top: 30px; }
    .game-card { 
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 15px; 
        border: 1px solid #e5e7eb;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    
    .res-card {
        padding: 30px;
        border-radius: 20px;
        text-align: center;
        color: white;
        min-height: 380px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .res-card-winner { 
        background: linear-gradient(135deg, #059669 0%, #10b981 100%); 
    }
    .res-card-loser { 
        background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%); 
    }
    .res-title { font-size: 1.6rem; font-weight: 700; margin-top: 15px; }
    .res-prob { font-size: 4.5rem; font-weight: 900; margin: 15px 0; }
    .res-odd { font-size: 1.2rem; font-weight: 500; opacity: 0.9; }
    .res-badge {
        background-color: rgba(255, 255, 255, 0.2);
        padding: 12px;
        border-radius: 12px;
        margin-top: 25px;
        font-weight: bold;
        font-size: 1.1rem;
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    .res-ev { font-size: 0.9rem; margin-top: 10px; opacity: 0.8; }

    .bet-result {
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        margin-top: 10px;
        font-weight: bold;
    }
    .news-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-left: 5px solid #ef4444;
        margin-bottom: 15px;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    div[data-testid="stImage"] { display: block; margin-left: auto; margin-right: auto; }
    
    .sidebar-season {
        text-align: center;
        color: #6b7280;
        font-size: 0.9rem;
        font-weight: bold;
        margin-top: -10px;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# Lógica de Classificação
def classificar_aposta_simples(prob, odd):
    ev = (prob * odd) - 1
    ev_percent = ev * 100
    if ev > 0.10 and prob > 0.65: return "💎 OURO", ev_percent
    elif ev > 0.05 and prob > 0.55: return "🥈 PRATA", ev_percent
    elif ev > 0: return "🥉 BRONZE", ev_percent
    else: return "⛔ SEM VALOR", ev_percent

def classificar_aposta(prob, odd):
    ev = (prob * odd) - 1
    if ev > 0.10 and prob > 0.65: return "💎 OURO", "#d1fae5", "#065f46"
    elif ev > 0.05 and prob > 0.55: return "🥈 PRATA", "#dbeafe", "#1e40af"
    elif ev > 0: return "🥉 BRONZE", "#fef3c7", "#92400e"
    else: return "⛔ SEM VALOR", "#fee2e2", "#991b1b"

def get_logo(team_name):
    name_clean = str(team_name).upper().strip()
    if name_clean in NBA_LOGOS: return NBA_LOGOS[name_clean]
    for key in NBA_LOGOS.keys():
        if name_clean in key: return NBA_LOGOS[key]
    return DEFAULT_LOGO

# === SIDEBAR ===
with st.sidebar:
    st.image("https://cdn.nba.com/logos/leagues/logo-nba.svg", width=120)
    st.markdown("<div class='sidebar-season'>TEMPORADA 2025-2026</div>", unsafe_allow_html=True)
    st.divider()
    st.title("🏀 Sniper Pro")
    st.info("Sistema operando com dados automáticos via GitHub Actions.")

@st.cache_resource
def load_system():
    if not os.path.exists("data/sistema_nba_v1.pkl"): return None
    return joblib.load("data/sistema_nba_v1.pkl")

# Carrega IA Engine
@st.cache_resource
def load_ia_engine():
    try:
        if XAIEngineNBA:
            return XAIEngineNBA("data/sistema_nba_v1.pkl")
    except: return None
    return None

sistema = load_system()
ia_engine = load_ia_engine()

if not sistema:
    st.error("⚠️ O sistema de IA ainda não foi treinado. Aguarde a primeira execução do robô.")
    st.stop()

modelo = sistema["modelo"]
stats = sistema["stats_atuais"]
features = sistema["variaveis"]
if pd.api.types.is_numeric_dtype(stats.index) and 'TEAM_NAME' in stats.columns:
    stats = stats.set_index('TEAM_NAME')

# === TÍTULO E ABAS ===
st.title("🏀 NBA SNIPER PRO")
tab1, tab2, tab3, tab4 = st.tabs(["📅 Jogos de Hoje", "🎮 Simulador Manual", "📰 Newsletter AI", "🚑 Lesões"])

# ABA 1: JOGOS DE HOJE
with tab1:
    arquivo_historico = "data/historico_previsoes.json"
    df_hoje = pd.DataFrame()
    data_mostrada = "Nenhuma"

    if os.path.exists(arquivo_historico):
        try:
            # Carrega todo o histórico
            df_full = pd.read_json(arquivo_historico)
            
            if not df_full.empty:
                # Tenta pegar a data de hoje
                hoje_str = datetime.now().strftime('%Y-%m-%d')
                
                # Filtra jogos de hoje
                df_hoje = df_full[df_full['DATA'] == hoje_str].copy()
                data_mostrada = hoje_str
                
                # Se não houver jogos hoje, pega a última data disponível
                if df_hoje.empty:
                    ultima_data = df_full['DATA'].max()
                    df_hoje = df_full[df_full['DATA'] == ultima_data].copy()
                    data_mostrada = ultima_data
                    st.info(f"Visualizando dados de: {data_mostrada} (Nenhum jogo encontrado para hoje)")
                else:
                    st.success(f"Visualizando jogos de hoje: {data_mostrada}")
        except Exception as e:
            st.error(f"Erro ao ler arquivo de histórico: {e}")
    else:
        st.warning("Arquivo de histórico não encontrado (data/historico_previsoes.json).")

    # Exibição dos Cards
    if not df_hoje.empty:
        # Garante colunas de probabilidades complementares
        if 'PROB_VISITANTE' not in df_hoje.columns: df_hoje['PROB_VISITANTE'] = 1 - df_hoje['PROB_CASA']
        if 'ODD_JUSTA_VISITANTE' not in df_hoje.columns: df_hoje['ODD_JUSTA_VISITANTE'] = 1 / df_hoje['PROB_VISITANTE']
        
        st.subheader(f"📋 Cardápio de Apostas ({len(df_hoje)} jogos)")
        
        # Iteração para criar cards
        for i, row in df_hoje.iterrows():
            with st.container():
                st.markdown(f"<div class='game-card'>", unsafe_allow_html=True)
                c1, c2, c3 = st.columns([1, 0.5, 1])
                with c1:
                    st.image(get_logo(row['CASA']), width=50)
                    st.markdown(f"*{row['CASA']}*")
                with c2: st.markdown("<h3 style='text-align:center; color:#ccc'>VS</h3>", unsafe_allow_html=True)
                with c3:
                    st.image(get_logo(row['VISITANTE']), width=50)
                    st.markdown(f"*{row['VISITANTE']}*")
                st.divider()
                col_casa, col_vis = st.columns(2)
                with col_casa:
                    st.metric("Probabilidade", f"{row['PROB_CASA']*100:.1f}%")
                    st.caption(f"Odd Justa: {row['ODD_JUSTA_CASA']:.2f}")
                    odd_real = st.number_input(f"Odd {row['CASA']}", 1.01, 20.0, 1.90, key=f"oc_{i}")
                    tipo, bg, txt = classificar_aposta(row['PROB_CASA'], odd_real)
                    st.markdown(f"<div class='bet-result' style='background-color:{bg}; color:{txt}'>{tipo}</div>", unsafe_allow_html=True)
                with col_vis:
                    st.metric("Probabilidade", f"{row['PROB_VISITANTE']*100:.1f}%")
                    st.caption(f"Odd Justa: {row['ODD_JUSTA_VISITANTE']:.2f}")
                    odd_real_v = st.number_input(f"Odd {row['VISITANTE']}", 1.01, 20.0, 1.90, key=f"ov_{i}")
                    tipo, bg, txt = classificar_aposta(row['PROB_VISITANTE'], odd_real_v)
                    st.markdown(f"<div class='bet-result' style='background-color:{bg}; color:{txt}'>{tipo}</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("Nenhuma previsão disponível para exibição.")

# ABA 2: SIMULADOR MANUAL (CORRIGIDO)
with tab2:
    st.markdown("### 🎮 Simulador de Matchups")
    col1, col2, col3 = st.columns([1, 0.5, 1])
    times_lista = sorted([str(x) for x in stats.index.unique().tolist()])
    with col1:
        time_casa = st.selectbox("Mandante (Casa)", times_lista, index=0)
        st.image(get_logo(time_casa), width=120)
        b2b_casa = st.checkbox("Cansado (B2B)?", key="b2b_c")
        odd_sim_casa = st.number_input("Odd Casa", value=1.90, step=0.05)
    with col2:
        st.markdown("<div class='vs-text'>VS</div>", unsafe_allow_html=True)
    with col3:
        times_vis = [t for t in times_lista if t != time_casa]
        time_fora = st.selectbox("Visitante (Fora)", times_vis, index=0)
        st.image(get_logo(time_fora), width=120)
        b2b_fora = st.checkbox("Cansado (B2B)?", key="b2b_v")
        odd_sim_fora = st.number_input("Odd Visitante", value=1.90, step=0.05)

    if st.button("🔥 SIMULAR MATCHUP AGORA", type="primary", use_container_width=True):
        try:
            # 1. Recupera estatísticas e calcula a parte Matemática
            s_casa = stats.loc[time_casa].iloc[0] if isinstance(stats.loc[time_casa], pd.DataFrame) else stats.loc[time_casa]
            s_fora = stats.loc[time_fora].iloc[0] if isinstance(stats.loc[time_fora], pd.DataFrame) else stats.loc[time_fora]
            
            # Cálculo de Fadiga para o Modelo
            fadiga = int(b2b_casa) - int(b2b_fora)
            input_data = {'const': 1.0, 'IS_HOME': 1, 'IS_B2B': fadiga}
            for col in features:
                if '_DIFF' in col:
                    base = col.replace('_DIFF', '_MEAN')
                    input_data[col] = s_casa.get(base, 0) - s_fora.get(base, 0)
            df_in = pd.DataFrame([input_data])
            for col in ['const'] + features:
                if col not in df_in.columns: df_in[col] = 0.0

            prob_casa = modelo.predict(df_in[['const'] + features])[0]
            prob_fora = 1.0 - prob_casa
            odd_justa_casa = 1.0 / prob_casa if prob_casa > 0 else 0
            odd_justa_fora = 1.0 / prob_fora if prob_fora > 0 else 0
            lbl_casa, ev_casa = classificar_aposta_simples(prob_casa, odd_sim_casa)
            lbl_fora, ev_fora = classificar_aposta_simples(prob_fora, odd_sim_fora)

            # Lógica de Cores dos Cards
            if prob_casa > prob_fora:
                cls_casa, cls_fora = "res-card-winner", "res-card-loser"
            else:
                cls_casa, cls_fora = "res-card-loser", "res-card-winner"

            # 2. Exibe os Cards de Resultado
            st.markdown("### Resultado da Análise")
            c_res1, c_res2 = st.columns(2)
            with c_res1:
                st.markdown(f"""<div class="res-card {cls_casa}">
                    <img src="{get_logo(time_casa)}" width="80">
                    <div class="res-title">{time_casa}</div>
                    <div class="res-prob">{prob_casa*100:.1f}%</div>
                    <div class="res-odd">Odd Justa: {odd_justa_casa:.2f}</div>
                    <div class="res-badge">{lbl_casa}</div>
                    <div class="res-ev">EV: {ev_casa:+.1f}%</div>
                </div>""", unsafe_allow_html=True)
            with c_res2:
                st.markdown(f"""<div class="res-card {cls_fora}">
                    <img src="{get_logo(time_fora)}" width="80">
                    <div class="res-title">{time_fora}</div>
                    <div class="res-prob">{prob_fora*100:.1f}%</div>
                    <div class="res-odd">Odd Justa: {odd_justa_fora:.2f}</div>
                    <div class="res-badge">{lbl_fora}</div>
                    <div class="res-ev">EV: {ev_fora:+.1f}%</div>
                </div>""", unsafe_allow_html=True)
            
            # 3. Geração de Gráficos e Texto IA
            if ia_engine:
                st.markdown("---")
                st.markdown("### 📊 Análise do Especialista")

                # Gera gráfico e métricas via Engine
                caminho_img, df_metricas = ia_engine.gerar_graficos(time_casa, time_fora, s_casa, s_fora)
                
                # Exibe Gráfico
                col_graf, col_tab = st.columns([1.2, 0.8])
                with col_graf:
                    st.image(caminho_img, use_container_width=True, caption="Performance Relativa (Azul: Casa / Vermelho: Fora)")
                with col_tab:
                    st.dataframe(df_metricas, use_container_width=True, hide_index=True)

                # Gera Texto da IA (Tratando B2B e Injeção de Contexto)
                id_analise = f"ai_{time_casa}_{time_fora}_{b2b_casa}_{b2b_fora}"
                
                if id_analise not in st.session_state:
                    with st.spinner("🤖 O Especialista está analisando o impacto tático e o cansaço..."):
                        try:
                            # CORREÇÃO CRUCIAL AQUI:
                            # 1. Montamos o prompt básico sem passar B2B (para não quebrar a função antiga)
                            prompt_base = ia_engine.montar_prompt(time_casa, time_fora, df_metricas, prob_casa)
                            
                            # 2. Injetamos o contexto de cansaço manualmente no texto do prompt
                            contexto_extra = ""
                            if b2b_casa or b2b_fora:
                                contexto_extra = "\n\n[SITUAÇÃO DE CANSAÇO]:\n"
                                if b2b_casa: contexto_extra += f"- O time {time_casa} jogou ontem (Back-to-Back). O modelo já descontou pontos na probabilidade, explique o impacto tático disso.\n"
                                if b2b_fora: contexto_extra += f"- O time {time_fora} jogou ontem (Back-to-Back). O modelo já descontou pontos na probabilidade, explique o impacto físico disso.\n"
                            
                            # 3. Enviamos o prompt combinado para o Gemini
                            st.session_state[id_analise] = ia_engine.gerar_texto_gemini(prompt_base + contexto_extra)
                        except Exception as e:
                            st.error(f"Erro na IA: {e}")
                
                # Exibe a Resenha
                if id_analise in st.session_state:
                    st.subheader("🎙️ Resenha do Especialista")
                    st.info(st.session_state[id_analise])

        except Exception as e: st.error(f"Erro no simulador: {e}")

# ABA 3: NEWSLETTER
with tab3:
    st.header("🗞️ Notícias da NBA")
    if os.path.exists("data/news_db.json"):
        try:
            with open("data/news_db.json", "r", encoding='utf-8') as f:
                news = json.load(f)
            for item in news:
                st.markdown(f"""<div class="news-card">
                    <h4>{item.get('title', 'Sem título')}</h4>
                    <p>{item.get('summary_ai', '')}</p>
                    <small><a href="{item.get('link','#')}" target="_blank">Ler mais</a></small>
                </div>""", unsafe_allow_html=True)
        except Exception as e: st.error(f"Erro: {e}")
    else: st.info("Nenhuma notícia disponível.")

# ABA 4: LESÕES
with tab4:
    st.header("🚑 Relatório de Lesões (ESPN)")
    if os.path.exists("data/injuries.csv"):
        try:
            df_inj = pd.read_csv("data/injuries.csv")
            if not df_inj.empty:
                col_filt, col_log = st.columns([3, 1])
                with col_filt:
                    time_sel = st.selectbox("Filtrar Time:", ["Todos"] + sorted(df_inj['Time'].unique().tolist()))
                with col_log:
                    logo_url = get_logo(time_sel) if time_sel != "Todos" else DEFAULT_LOGO
                    st.image(logo_url, width=80)

                df_f = df_inj if time_sel == "Todos" else df_inj[df_inj['Time'] == time_sel]
                st.dataframe(df_f[['Time', 'Jogador', 'Status', 'Detalhes']], use_container_width=True, hide_index=True)
            else: st.success("Nenhuma lesão registrada.")
        except Exception as e: st.error(f"Erro: {e}")
    else: st.warning("Arquivo de lesões não encontrado.")