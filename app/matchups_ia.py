import os
from dotenv import load_dotenv
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from difflib import get_close_matches
from google import genai

# =====================================================
# CONFIGURAÇÃO INICIAL
# =====================================================
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY_2")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY_2 não encontrada no ambiente.")

client = genai.Client(api_key=GEMINI_API_KEY)

# =====================================================
# ENGINE XAI NBA
# =====================================================

class XAIEngineNBA:

    def __init__(self, caminho_sistema="data/sistema_nba_v1.pkl"):
        sistema = joblib.load(caminho_sistema)
        self.modelo = sistema["modelo"]
        self.stats = sistema["stats_atuais"]
        self.features = sistema["variaveis"]

        if "TEAM_NAME" in self.stats.columns:
            self.stats["TEAM_NAME"] = self.stats["TEAM_NAME"].str.upper().str.strip()
            self.stats = self.stats.set_index("TEAM_NAME")
        self.stats.index = self.stats.index.str.upper().str.strip()

    def normalizar_time(self, nome):
        nome = nome.upper().strip()
        if nome in self.stats.index: return nome
        sugestao = get_close_matches(nome, self.stats.index.tolist(), n=1, cutoff=0.6)
        if sugestao: return sugestao[0]
        raise ValueError(f"Time '{nome}' não encontrado.")

    def obter_stats_times(self, time_a, time_b):
        time_a, time_b = self.normalizar_time(time_a), self.normalizar_time(time_b)
        s_a, s_b = self.stats.loc[time_a], self.stats.loc[time_b]
        if isinstance(s_a, pd.DataFrame): s_a = s_a.iloc[0]
        if isinstance(s_b, pd.DataFrame): s_b = s_b.iloc[0]
        return time_a, time_b, s_a, s_b

    def calcular_probabilidade(self, s_casa, s_fora):
        # Nota: O cálculo de probabilidade puro do modelo não recebe B2B aqui
        # O B2B é injetado manualmente no App antes de chamar a predição
        input_data = {"const": 1.0, "IS_HOME": 1, "IS_B2B": 0} 
        for col in self.features:
            if "_DIFF" in col:
                base = col.replace("_DIFF", "_MEAN")
                input_data[col] = s_casa.get(base, 0) - s_fora.get(base, 0)
        df_in = pd.DataFrame([input_data])
        for col in ["const"] + self.features:
            if col not in df_in.columns: df_in[col] = 0.0
        return self.modelo.predict(df_in[["const"] + self.features])[0]

    def calcular_rating_manual(self, stats, tipo="OFF"):
        pts = stats.get("PTS_MEAN", 0)
        fga = stats.get("FGA_MEAN", 0)
        fta = stats.get("FTA_MEAN", 0)
        tov = stats.get("TOV_MEAN", 0)
        oreb = stats.get("OREB_MEAN", 0)
        posses = fga + (0.44 * fta) + tov - oreb
        return (pts / posses) * 100 if posses > 0 else 0

    def gerar_graficos(self, time_a, time_b, s_a, s_b, salvar_em="comparacao_xai.png"):
        COR_A, COR_B = '#1D428A', '#C9082A'
        
        def buscar_val(stats_row, prefixos, tipo_rating=None):
            for p in prefixos:
                if p in stats_row.index: return stats_row[p]
            return self.calcular_rating_manual(stats_row, tipo_rating) if tipo_rating else 0

        metricas_plot = [
            ("Pontos", ["PTS_MEAN"]),
            ("Eficiência Ofensiva", ["OFF_RATING_MEAN", "ORTG_MEAN"], "OFF"),
            ("Eficiência Defensiva", ["DEF_RATING_MEAN", "DRTG_MEAN"], "DEF"),
            ("Rebotes", ["REB_MEAN"]),
            ("Turnovers", ["TOV_MEAN"])
        ]

        dados = [{"Métrica": l, time_a: buscar_val(s_a, c, r[0] if r else None), time_b: buscar_val(s_b, c, r[0] if r else None)} for l, c, *r in metricas_plot]
        df = pd.DataFrame(dados)

        fig, axes = plt.subplots(2, 1, figsize=(10, 8))
        x = np.arange(len(df))
        axes[0].bar(x - 0.2, df[time_a], 0.4, label=time_a, color=COR_A)
        axes[0].bar(x + 0.2, df[time_b], 0.4, label=time_b, color=COR_B)
        axes[0].set_xticks(x); axes[0].set_xticklabels(df["Métrica"]); axes[0].legend()
        axes[1].barh(x - 0.2, df[time_a], 0.4, label=time_a, color=COR_A)
        axes[1].barh(x + 0.2, df[time_b], 0.4, label=time_b, color=COR_B)
        axes[1].set_yticks(x); axes[1].set_yticklabels(df["Métrica"]); axes[1].legend()

        plt.tight_layout(); plt.savefig(salvar_em, dpi=100); plt.close()
        return salvar_em, df

    # === AQUI ESTAVA O ERRO: ESTAS FUNÇÕES DEVEM ESTAR DENTRO DA CLASSE ===
    def montar_prompt(self, time_a, time_b, df, prob_a, is_b2b=0):
        favorito = time_a if prob_a > 0.5 else time_b
        return f"""
Você é comentarista da NBA estilo ESPN.
Dados do jogo: {time_a} vs {time_b}.
Estatísticas:
{df.to_string(index=False)}
Probabilidade de vitória do {time_a}: {prob_a*100:.1f}%.

Explique por que o {favorito} é favorito e mencione as Eficiências.
"""

    def gerar_texto_gemini(self, prompt):
        try:
            response = client.models.generate_content(
            model="gemini-2.0-flash",
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            return f"Erro ao gerar texto: {e}"

    def analisar_matchup(self, time_a, time_b):
        time_a, time_b, s_a, s_b = self.obter_stats_times(time_a, time_b)
        prob_a = self.calcular_probabilidade(s_a, s_b)
        img, df = self.gerar_graficos(time_a, time_b, s_a, s_b)
        texto = self.gerar_texto_gemini(self.montar_prompt(time_a, time_b, df, prob_a))
        return {"time_a": time_a, "time_b": time_b, "prob_time_a": prob_a, "grafico": img, "explicacao": texto}