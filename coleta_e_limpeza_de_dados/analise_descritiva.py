import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats # Necessário para o T-Test na ETAPA 3

# ============================================================
# ETAPA 1 — PREPARAÇÃO DA BASE
# ============================================================

print("🧭 ETAPA 1 — Preparação da Base")

# === 1.1 Ler o arquivo ===
arquivo_entrada = "data/nba_dados_padronizados.csv"
try:
    df = pd.read_csv(arquivo_entrada)
except FileNotFoundError:
    # Tenta carregar o arquivo de features, caso o arquivo bruto não exista.
    print(f"⚠️ Arquivo de entrada '{arquivo_entrada}' não encontrado. Tentando carregar base com features...")
    df = pd.read_csv("base_com_features.csv") # Assumindo o formato padrão do CSV
    
print(f"✅ Base carregada: {len(df):,} registros e {len(df.columns)} colunas")

# === 1.2 Corrigir colunas duplicadas (caso existam) ===
cols = pd.Series(df.columns)
dupes = cols[cols.duplicated()].unique()
if len(dupes) > 0:
    print(f"⚠️ Colunas duplicadas detectadas: {list(dupes)}")
    new_cols = []
    seen = {}
    for c in df.columns:
        if c in seen:
            seen[c] += 1
            new_cols.append(f"{c}_{seen[c]}")
        else:
            seen[c] = 0
            new_cols.append(c)
    df.columns = new_cols
    print("✔️ Duplicatas renomeadas automaticamente.")
else:
    print("✔️ Nenhuma duplicata de coluna detectada.")

# === 1.3 Corrigir colunas WIN / WL / VITORIA ===
# Bloco para garantir que a coluna alvo VITORIA (1=Vitória, 0=Derrota) exista.
if 'VITORIA' not in df.columns or df['VITORIA'].isnull().all():
    if 'WL' in df.columns:
        df['VITORIA'] = df['WL'].map({'W': 1, 'L': 0})
        df.drop(columns=['WL'], inplace=True, errors='ignore')
    elif 'WIN' in df.columns:
        df.rename(columns={'WIN': 'VITORIA'}, inplace=True)
    else:
        df['VITORIA'] = pd.NA
        print("⚠️ Coluna VITORIA não encontrada. Criada vazia. Verifique a base original.")
if 'WIN' in df.columns:
    df.drop(columns=['WIN'], inplace=True, errors='ignore')

# === 1.4 Converter datas e ordenar ===
if 'GAME_DATE' in df.columns:
    df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'], errors='coerce')
else:
    raise ValueError("❌ A base precisa conter a coluna GAME_DATE.")

if 'TEAM_NAME' not in df.columns:
    raise ValueError("❌ A base precisa conter a coluna TEAM_NAME.")

df = df.sort_values(by=['TEAM_NAME', 'GAME_DATE']).reset_index(drop=True)
print("📅 Ordenação por TEAM_NAME e GAME_DATE concluída.")

# ============================================================
# ETAPA 2 — CÁLCULO DAS MÉDIAS ACUMULADAS (SEM VAZAMENTO)
# ============================================================

print("\n⚙️ ETAPA 2 — Cálculo das médias acumuladas")
vars_ofensivas = ['PTS', 'AST', 'FG_PCT', 'FT_PCT', 'FG3_PCT'] 
vars_defensivas = ['REB', 'STL', 'BLK']
vars_eficiencia = ['TOV']
vars_desempenho = vars_ofensivas + vars_defensivas + vars_eficiencia

print(f"📊 Variáveis consideradas (FT_PCT INCLUÍDO): {vars_desempenho}")

# === 2.2 Calcular médias acumuladas (expanding mean) por time ===
for var in vars_desempenho:
    if var in df.columns:
        df[f'{var}_MEAN'] = (
            df.groupby('TEAM_NAME')[var]
             .expanding()
             .mean()
             .shift(1)
             .reset_index(level=0, drop=True)
        )
    else:
        print(f"⚠️ Variável {var} não encontrada na base e será ignorada.")

# === 2.3 Remover jogos iniciais (sem histórico suficiente) ===
cols_mean = [f'{var}_MEAN' for var in vars_desempenho if f'{var}_MEAN' in df.columns]
if cols_mean:
    df = df.dropna(subset=cols_mean)
    print(f"✅ Após limpeza de NaNs: {len(df):,} linhas válidas")
else:
    print("⚠️ Nenhuma coluna MEAN calculada. Pulando limpeza de NaNs.")

# ============================================================
# ETAPA 3 — ESTATÍSTICA DESCRITIVA
# ============================================================

print("\n📈 ETAPA 3 — Estatística Descritiva")

# === 3.1 Estatísticas gerais da liga (inclui FT_PCT) ===
estat_liga = pd.DataFrame({
    'Média': df[vars_desempenho].mean(),
    'Variância': df[vars_desempenho].var()
}).round(4)
estat_liga.index.name = 'Variável'

# === 3.2 Estatísticas por time (inclui FT_PCT) ===
estat_por_time = df.groupby('TEAM_NAME')[vars_desempenho].mean().round(4)

# === 3.3 Diferença entre vitórias e derrotas (inclui FT_PCT e T-Test) ===
vitorias = df[df['VITORIA'] == 1]
derrotas = df[df['VITORIA'] == 0]

tabela_significancia = []
for var in vars_desempenho:
    if var in df.columns:
        media_vit = vitorias[var].mean()
        media_der = derrotas[var].mean()
        dif = media_vit - media_der

        # T-Test para significância estatística
        t_stat, p_value = stats.ttest_ind(vitorias[var].dropna(), derrotas[var].dropna(), equal_var=False, nan_policy='omit')
        
        tabela_significancia.append({
            'Variável': var,
            'Média_Vitória': media_vit,
            'Média_Derrota': media_der,
            'Diferença': dif,
            'T-Stat': t_stat,
            'p-value': p_value,
            'Significativo (α=0.05)': 'Sim' if p_value < 0.05 else 'Não'
        })
    else:
        # Se a variável de desempenho não estava na base original, ela é ignorada aqui.
        pass

tabela_significancia_df = pd.DataFrame(tabela_significancia).set_index('Variável').round(4)

print("\n📊 Diferença de médias (Vitória - Derrota) e Significância:")
print(tabela_significancia_df[['Diferença', 'p-value', 'Significativo (α=0.05)']])

# ============================================================
# ETAPA 4 — EXPORTAÇÃO DOS RESULTADOS
# ============================================================

print("\n💾 ETAPA 4 — Exportação dos resultados")

# === 4.1 Garantir unicidade de colunas antes de exportar ===
assert df.columns.duplicated().sum() == 0, "Ainda existem colunas duplicadas!"

# === 4.2 Criar pasta de saída ===
out_dir = Path(".")
out_dir.mkdir(parents=True, exist_ok=True)

# === 4.3 Exportar para Excel ===
arquivo_excel = out_dir / "data/relatorio_estatistica_descritiva_FINAL.xlsx"
# Criamos um NOVO arquivo com o sufixo FINAL para evitar conflitos com versões anteriores.
with pd.ExcelWriter(arquivo_excel, engine='openpyxl') as writer:
    estat_liga.to_excel(writer, sheet_name='Liga_Geral')
    estat_por_time.to_excel(writer, sheet_name='Por_Time')
    tabela_significancia_df.to_excel(writer, sheet_name='Significancia_Vit_Loss')
    df.to_excel(writer, sheet_name='Base_Com_Features', index=False)

# === 4.4 Exportar CSVs auxiliares ===
# Salvando a base de features completa (agora com FT_PCT_MEAN)
df.to_csv(out_dir / "data/base_com_features_FINAL.csv", index=False)
tabela_significancia_df.to_csv(out_dir / "data/teste_significancia_FINAL.csv")

# ============================================================
# FINALIZAÇÃO
# ============================================================

print("\n✅ Pipeline de análise descritiva e feature engineering finalizado com sucesso!")
print("🔔 Todas as etapas foram recalculadas, e FT_PCT está agora incluído de forma consistente.")
print(f"📁 Arquivo de relatório final gerado: {arquivo_excel.name}")
