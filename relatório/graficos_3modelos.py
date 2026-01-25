import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ============================
#  DADOS DAS MÉTRICAS
# ============================
dados = {
    "Cenário": [
        "Cenario_A (Teste 24)",
        "Cenario_B (Teste 25)",
        "Cenario_Geral"
    ],
    "Acc_LogReg": [0.550, 0.624, 0.588],
    "Acc_RF": [0.575, 0.614, 0.802],
    "Acc_XGB": [0.585, 0.619, 0.633],
    "AUC_LogReg": [0.583, 0.655, 0.624],
    "AUC_RF": [0.611, 0.650, 0.887],
    "AUC_XGB": [0.612, 0.651, 0.685]
}

df = pd.DataFrame(dados)
df.set_index("Cenário", inplace=True)

# ============================
#  HEATMAP (Frio → Quente)
# ============================
plt.figure(figsize=(12, 6))
sns.heatmap(
    df,
    annot=True,
    fmt=".3f",
    cmap="coolwarm",       # <--- ESCALA FRIA → QUENTE
    linewidths=0.5
)

plt.title("Heatmap de Performance dos Modelos (Acurácia e AUC)", fontsize=14)
plt.ylabel("Cenário")
plt.tight_layout()

# SALVAR EM ALTA QUALIDADE
plt.savefig("heatmap_modelos.png", dpi=300, bbox_inches="tight")
plt.show()

print("Heatmap salvo como: heatmap_modelos.png")


# ============================
#  GRÁFICOS INDIVIDUAIS
# ============================

# --- Acurácia por Modelo ---
plt.figure(figsize=(10, 5))
df[["Acc_LogReg", "Acc_RF", "Acc_XGB"]].plot(kind="bar")
plt.title("Acurácia dos Modelos por Cenário")
plt.ylabel("Acurácia")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig("acuracia_modelos.png", dpi=300, bbox_inches="tight")
plt.show()

# --- AUC por Modelo ---
plt.figure(figsize=(10, 5))
df[["AUC_LogReg", "AUC_RF", "AUC_XGB"]].plot(kind="bar")
plt.title("AUC dos Modelos por Cenário")
plt.ylabel("AUC")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig("auc_modelos.png", dpi=300, bbox_inches="tight")
plt.show()

# ============================
#  SALVAR EXCEL
# ============================

df.to_excel("metricas_modelos.xlsx", index=True)
print("Arquivo Excel salvo como: metricas_modelos.xlsx")

