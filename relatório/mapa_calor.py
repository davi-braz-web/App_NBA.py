import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path

# --- 1. CARREGAR A MATRIZ DE CORRELAÇÃO ---
# Carrega o arquivo CSV que foi gerado no passo anterior
arquivo_csv_correlacao = Path("data/matriz_correlacao.csv")

try:
    # Lendo com o formato correto (sep=';', decimal=',')
    correlacao_df = pd.read_csv(arquivo_csv_correlacao, sep=';', decimal=',', index_col=0)
    print(" ✅ Matriz de Correlação carregada para visualização.")
except FileNotFoundError:
    print(f" ❌ ERRO: Arquivo '{arquivo_csv_correlacao}' não encontrado.")
    exit()

# --- 2. GERAR O MAPA DE CALOR (HEATMAP) ---

plt.figure(figsize=(10, 8))
sns.heatmap(
    correlacao_df,
    annot=True,        # Mostrar os valores de correlação
    fmt=".2f",         # Formato com 2 casas decimais
    cmap='coolwarm',   # Esquema de cores (azul frio para negativo, vermelho quente para positivo)
    linewidths=.5,     # Linhas entre as células
    cbar_kws={'label': 'Coeficiente de Correlação de Pearson'}
)
plt.title('Mapa de Calor da Matriz de Correlação entre Variáveis de Desempenho e Vitória')
plt.show()

# --- 3. FOCAR NA CORRELAÇÃO COM A VARIÁVEL ALVO (VITORIA) ---
# Extrai e ordena a correlação com 'VITORIA'
if 'VITORIA' in correlacao_df.index:
    corr_vitoria = correlacao_df['VITORIA'].sort_values(ascending=False)
    print("\n 📈 Correlação com a variável 'VITORIA':")
    print(corr_vitoria)
else:
    print("\n ⚠️ A coluna 'VITORIA' não está presente na matriz para análise direta.")