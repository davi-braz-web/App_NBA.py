# Arquivo: update_injuries.py
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

# URL da ESPN (Geralmente mais estável para scraping de tabelas)
URL = "https://www.espn.com/nba/injuries"

print(f"🚑 Iniciando coleta de lesões via ESPN ({URL})...")

def get_injuries_safe():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(URL, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        lista_lesoes = []
        
        # A ESPN organiza em seções 'ResponsiveTable'
        sections = soup.find_all('div', class_='ResponsiveTable')
        
        if not sections:
            print("⚠️ Nenhuma tabela encontrada. A estrutura do site pode ter mudado.")
            return pd.DataFrame()

        for section in sections:
            try:
                # 1. Tenta achar o nome do time no cabeçalho da tabela
                # Geralmente está numa classe 'Table__Title'
                team_header = section.find('div', class_='Table__Title')
                if not team_header:
                    continue # Pula se não achar nome do time
                
                team_name = team_header.text.strip()
                
                # 2. Processa as linhas da tabela
                rows = section.find_all('tr')
                
                # Pula a primeira linha (cabeçalho das colunas: NAME, STATUS, etc)
                for row in rows[1:]:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        # Extração segura dos dados
                        nome_jog = cols[0].get_text(strip=True)
                        
                        # A coluna 1 geralmente é o status (Out, Day-To-Day)
                        status_raw = cols[1].get_text(strip=True)
                        
                        # A coluna 2 ou 3 pode ser a data ou comentário
                        detalhes = cols[2].get_text(strip=True) if len(cols) > 2 else ""
                        
                        # Normalização simples do status
                        status = "Unknown"
                        if 'Out' in status_raw: status = 'Out'
                        elif 'Day' in status_raw: status = 'Day-to-Day'
                        elif 'Questionable' in status_raw: status = 'Questionable'
                        elif 'Doubtful' in status_raw: status = 'Doubtful'
                        
                        lista_lesoes.append({
                            'Time': team_name,
                            'Jogador': nome_jog,
                            'Status': status_raw, # Mantém o original para exibição
                            'Detalhes': detalhes,
                            'Data_Coleta': datetime.now().strftime('%Y-%m-%d %H:%M')
                        })
            except Exception as e:
                # Se der erro num time específico, avisa mas continua para o próximo
                print(f"⚠️ Erro ao processar um time: {e}")
                continue

        return pd.DataFrame(lista_lesoes)

    except Exception as e:
        print(f"❌ Erro crítico de conexão: {e}")
        return pd.DataFrame()

# Execução Principal
if __name__ == "__main__":
    df = get_injuries_safe()
    
    if not df.empty:
        df.to_csv("data/injuries.csv", index=False)
        print(f"✅ Sucesso! {len(df)} registros salvos em 'data/injuries.csv'.")
        print("Amostra dos dados:")
        print(df.head(3))
    else:
        print("⚠️ Nenhum dado coletado. Criando arquivo vazio para evitar erro no App.")
        # Cria arquivo vazio com cabeçalho correto
        pd.DataFrame(columns=['Time', 'Jogador', 'Status', 'Detalhes', 'Data_Coleta']).to_csv("data/injuries.csv", index=False)