import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix

# Configuração de Estilo
sns.set_theme(style="white")
COLOR_PALETTE = "Blues"

def plot_matrix(y_true, y_pred, title, ax):
    cm = confusion_matrix(y_true, y_pred)
    sns.heatmap(cm, annot=True, fmt='d', cmap=COLOR_PALETTE, ax=ax, cbar=False,
                annot_kws={"size": 14, "weight": "bold"})
    # Título com ajuste de posição (pad) para não bater no eixo
    ax.set_title(title, fontsize=11, fontweight='bold', pad=15)
    ax.set_xticklabels(['Derrota', 'Vitória'])
    ax.set_yticklabels(['Derrota', 'Vitória'])
    ax.set_xlabel('Previsão', fontsize=10)
    ax.set_ylabel('Real', fontsize=10)

def treinar_e_prever(df, train_years, test_year, features):
    train = df[df['YEAR'].isin(train_years)].dropna(subset=features + ['VITORIA'])
    test = df[df['YEAR'] == test_year].dropna(subset=features + ['VITORIA'])
    
    if train.empty or test.empty:
        return None, None
        
    X_train = sm.add_constant(train[features])
    X_test = sm.add_constant(test[features])
    
    model = sm.Logit(train['VITORIA'], X_train).fit(disp=0)
    y_pred = (model.predict(X_test) > 0.5).astype(int)
    return test['VITORIA'], y_pred

# --- CARREGAMENTO ---
df_final = pd.read_csv('data/dbase_com_features_FINAL.csv')
df_final['GAME_DATE'] = pd.to_datetime(df_final['GAME_DATE'])
df_final['YEAR'] = df_final['GAME_DATE'].dt.year
vars_base = ['PTS_MEAN', 'REB_MEAN', 'AST_MEAN', 'STL_MEAN', 'BLK_MEAN', 'TOV_MEAN', 'FG_PCT_MEAN', 'FT_PCT_MEAN', 'FG3_PCT_MEAN']

# ============================================================
# IMAGEM 1: QUADRANTE DE CENÁRIOS (Corrigido Overlap)
# ============================================================
fig, axes = plt.subplots(2, 2, figsize=(13, 11)) # Aumentado ligeiramente o tamanho
fig.suptitle('Matrizes de Confusão por Cenário', fontsize=16, fontweight='bold', y=0.98)

# Cenários
scenarios = [
    ([2022, 2023], 2024, "1) Treino: 22/23 -> Teste: 24"),
    ([2023, 2024], 2025, "2) Treino: 23/24 -> Teste: 25"),
    ([2022, 2023, 2024], 2025, "3) Treino: 22/23/24 -> Teste: 25"),
    (df_final['YEAR'].unique()[df_final['YEAR'].unique() < 2025], 2025, "4) Cenário Geral (Histórico -> 25)")
]

for i, (train_y, test_y, title) in enumerate(scenarios):
    ax = axes[i // 2, i % 2]
    y_real, y_pred = treinar_e_prever(df_final, train_y, test_y, vars_base)
    if y_real is not None:
        plot_matrix(y_real, y_pred, title, ax)

# AJUSTE FINO DE ESPAÇAMENTO (Resolve a sobreposição)
plt.subplots_adjust(hspace=0.4, wspace=0.3, top=0.90, bottom=0.08, left=0.1, right=0.9)

plt.savefig('quadrante_cenarios_corrigido.png', dpi=300, bbox_inches='tight')
plt.show()

# O Modelo Avançado (Cenário 5) permanece igual, já que você aprovou