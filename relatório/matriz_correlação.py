import pandas as pd
from pathlib import Path
from openpyxl import load_workbook

# === 1. PARÂMETROS E CARREGAMENTO DA BASE ===
print(" 🧭  Iniciando cálculo e exportação da Correlação...")

arquivo_entrada_base = "data/dbase_com_features.csv"
arquivo_entrada_relatorio = "data/relatorio_estatistica_descritiva.xlsx"

try:
    # CORREÇÃO CRÍTICA AQUI: Define o separador (sep=';') e o decimal (decimal=',')
    df = pd.read_csv(arquivo_entrada_base, sep=';', decimal=',')
    print(f" ✅  Base carregada com {len(df):,} linhas.")
except FileNotFoundError:
    print(f" ❌  ERRO: Arquivo '{arquivo_entrada_base}' não encontrado. Certifique-se de executar a 'Análise Descritiva' primeiro.")
    exit()
except Exception as e:
    print(f" ❌  ERRO NA LEITURA DO CSV: {e}")
    print(" ⚠️  Verifique se o arquivo CSV está corretamente formatado (separador ';' e decimal ',').")
    exit()

# === 2. VERIFICAÇÃO E DEFINIÇÃO DAS VARIÁVEIS ===
# Variáveis de Desempenho esperadas
vars_esperadas = ['VITORIA', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV',
                   'FG_PCT', 'FT_PCT', 'FG3_PCT', 'PLUS_MINUS']

# Verifica quais das variáveis esperadas estão realmente no DataFrame
vars_disponiveis = [var for var in vars_esperadas if var in df.columns]

if not vars_disponiveis:
    print("\n ❌  ERRO CRÍTICO: Nenhuma das colunas de desempenho esperadas foi encontrada.")
    print(f" 📋  Colunas presentes na base: {list(df.columns)}")
    print(" 🛠️  Ajuste o script de 'Análise Descritiva' para garantir que as colunas sejam mantidas.")
    exit()

# Define as variáveis para correlação como as disponíveis
vars_correlacao = vars_disponiveis
print(f" 📊  Variáveis disponíveis para correlação: {vars_correlacao}")

# === 3. CÁLCULO DA MATRIZ DE CORRELAÇÃO ===
# Garante que as colunas são numéricas antes de calcular a correlação
try:
    correlacao = df[vars_correlacao].apply(pd.to_numeric, errors='coerce').corr().round(4)
    correlacao.index.name = 'Variável'

    print("\n ✅  Matriz de Correlação (Pearson) calculada:")
    print(correlacao)
except Exception as e:
    print(f" ❌  ERRO no cálculo da correlação: {e}")
    print(" ⚠️  Mesmo com o ajuste de leitura, algumas colunas podem conter caracteres não numéricos. Verifique a limpeza de dados.")
    exit()


# === 4. EXPORTAÇÃO E ATUALIZAÇÃO DOS ARQUIVOS ===
out_dir = Path(".")
out_dir.mkdir(parents=True, exist_ok=True)
arquivo_excel_final = out_dir / arquivo_entrada_relatorio
arquivo_csv_correlacao = out_dir / "matriz_correlacao.csv"

# 4.1 Exportar para CSV
# Nota: Usando 'decimal=',' e 'sep=';' para manter a consistência do formato de saída
correlacao.to_csv(arquivo_csv_correlacao, sep=';', decimal=',')
print(f"\n 💾  Matriz de Correlação salva como: {arquivo_csv_correlacao}")

# 4.2 Atualizar o arquivo Excel (relatorio_estatistica_descritiva.xlsx)
try:
    with pd.ExcelWriter(arquivo_excel_final, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        correlacao.to_excel(writer, sheet_name='Correlacao')
    print(f" 📝  Planilha 'Correlacao' adicionada/atualizada no relatório: {arquivo_excel_final}")
except FileNotFoundError:
    print(f" ⚠️  Arquivo de relatório '{arquivo_entrada_relatorio}' não encontrado. Criando novo arquivo apenas com a correlação.")
    with pd.ExcelWriter(arquivo_excel_final, engine='openpyxl') as writer:
        correlacao.to_excel(writer, sheet_name='Correlacao')

print("\n ✅  Cálculo de Correlação finalizado com sucesso!")