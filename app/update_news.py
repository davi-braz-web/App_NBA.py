import feedparser
from google import genai
import json
import os
from dotenv import load_dotenv
from datetime import datetime
import time

# =====================================================
# GEMINI — CHAVE 1 (NOTÍCIAS)
# =====================================================
load_dotenv(override=True)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY_1_NEWS")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY_1_NEWS não encontrada no ambiente.")

client = genai.Client(api_key=GEMINI_API_KEY)

# =====================================================
# FEEDS
# =====================================================

RSS_FEEDS = {
    "🇺🇸 ESPN NBA": "https://www.espn.com/espn/rss/nba/news",
    "🇧🇷 Jumper Brasil": "https://jumperbrasil.com.br/feed/",
}

# =====================================================
# RESUMO COM IA
# =====================================================

def resumir_com_ia(titulo, texto):
    prompt = f"""
Aja como analista da NBA.

Regras:
- Traduza para PT-BR
- Resuma em até 3 linhas
- Destaque impacto esportivo

Notícia: {titulo}
Texto: {texto}
"""

    response = client.models.generate_content(
        model="models/gemini-2.0-flash",
        contents=prompt
    )

    return response.text.strip()

# =====================================================
# PIPELINE
# =====================================================

def run_news_update():
    print("\n📰 Atualizando notícias com IA...\n")

    news_data = []

    for nome_site, url in RSS_FEEDS.items():
        print(f"-> Lendo {nome_site}")
        feed = feedparser.parse(url)

        # Pega as 2 notícias mais recentes de cada feed
        for entry in feed.entries[:2]:
            conteudo = entry.get("summary", "") or entry.get("title", "")
            
            try:
                resumo = resumir_com_ia(entry.title, conteudo)
                
                news_item = {
                    "source": nome_site,
                    "title": entry.title,
                    "link": entry.link,
                    "summary_ai": resumo,
                    "date": datetime.now().strftime("%d/%m %H:%M")
                }
                news_data.append(news_item)
                time.sleep(1) # Evita sobrecarga na API
            except Exception as e:
                print(f"⚠️ Erro ao resumir notícia '{entry.title}': {e}")

    # === CORREÇÃO: Caminho alterado para a pasta data ===
    if news_data:
        caminho_arquivo = "data/noticias_nba.json"
        with open(caminho_arquivo, "w", encoding="utf-8") as f:
            json.dump(news_data, f, ensure_ascii=False, indent=4)
        print(f"\n✅ Sucesso! {len(news_data)} notícias salvas em: {caminho_arquivo}")
    else:
        print("❌ Nenhuma notícia coletada.")

if __name__ == "__main__":
    run_news_update()