import pandas as pd
import matplotlib.pyplot as plt

# 1. Preparação dos dados da Tabela de Coeficientes [cite: 518, 522, 528, 496, 497, 499, 500]
coeffs_data = {
    "Variável": ["Eficiência (FG_PCT_DIFF)", "Fator Casa (IS_HOME)", "Roubos (STL_MEAN)", 
                 "Rebotes (REB_MEAN)", "Volume (PTS_MEAN)", "Turnovers (TOV_MEAN)", "Fadiga (IS_B2B)"],
    "Odds Ratio (OR)": [14.34, 1.536, 1.09, 1.08, 0.962, 0.917, 0.77],
    "Impacto %": ["+1334.0%", "+53.6%", "+9.0%", "+8.0%", "-3.8%", "-8.3%", "-23.0%"],
    "Significância": ["p < 0.001", "p < 0.001", "p < 0.05", "p < 0.05", "p < 0.05", "p < 0.05", "p < 0.001"]
}
df_coeffs = pd.DataFrame(coeffs_data)

# 2. Preparação dos dados da Tabela de Cenários [cite: 547, 579]
scenarios_data = {
    "Modelo": ["Regressão Logística", "Random Forest", "XGBoost"],
    "Cenário A (2024)": ["~55.0%", "~57.5%", "~58.5%"],
    "Cenário B (2025)": ["62.36%", "61.43%", "61.87%"],
    "Cenário Geral": ["~59.0%", "80.20%", "~63.5%"]
}
df_scenarios = pd.DataFrame(scenarios_data)

def save_table_as_image(df, filename, title):
    fig, ax = plt.subplots(figsize=(10, len(df)*0.6 + 1))
    ax.axis('off')
    ax.set_title(title, fontweight='bold', pad=20)
    table = ax.table(cellText=df.values, colLabels=df.columns, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.5)
    
    # Estilização Profissional
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_text_props(weight='bold', color='white')
            cell.set_facecolor('#2c3e50')
        elif row > 0:
            cell.set_facecolor('#ecf0f1' if row % 2 == 0 else 'white')
            
    plt.savefig(filename, bbox_inches='tight', dpi=300)

# Execução
save_table_as_image(df_coeffs, 'tabela_coeficientes_final.png', 'Tabela 1: Coeficientes e Impactos do Modelo Final')
save_table_as_image(df_scenarios, 'tabela_cenarios_comparativa.png', 'Tabela 2: Performance Preditiva por Modelo e Cenário')