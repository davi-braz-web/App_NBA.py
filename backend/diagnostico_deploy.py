import os
import sys
import glob
import pandas as pd
import joblib
import traceback

def list_files():
    print("\n➡️  PASTA ATUAL:")
    try:
        print(os.getcwd())
    except Exception as e:
        print("  Erro ao obter cwd:", e)

    print("\n➡️  ARQUIVOS NA PASTA (primeiros 200):")
    for i, f in enumerate(sorted(glob.glob("*"))):
        if i >= 200:
            break
        print(" ", f)

def check_csv(filename):
    print(f"\n--- Verificando: {filename} ---")
    if not os.path.exists(filename):
        print(" ❌ NÃO ENCONTRADO")
        return False
    try:
        # tenta inferir separador lendo primeiras 2000 bytes
        with open(filename, "r", encoding="utf-8", errors="ignore") as fh:
            sample = fh.read(2000)
        # heurística simples
        sep = ',' if sample.count(',') >= sample.count(';') else ';'
        print(f"  -> Encontrado. Aparenta usar separador '{sep}'")
        df = pd.read_csv(filename, sep=sep, nrows=5)
        print("  -> Colunas (até 20):", df.columns.tolist()[:20])
        print("  -> Primeiras linhas:")
        print(df.head(3).to_string(index=False))
        return True
    except Exception as e:
        print("  ❌ Erro ao ler CSV:", e)
        traceback.print_exc()
        return False

def check_pickle(pklname):
    print(f"\n--- Verificando pickle: {pklname} ---")
    if not os.path.exists(pklname):
        print(" ❌ Pickle não encontrado")
        return
    try:
        pacote = joblib.load(pklname)
        print("  -> Pickle carregado com chaves:", list(pacote.keys()) if isinstance(pacote, dict) else type(pacote))
        if isinstance(pacote, dict) and "stats_atuais" in pacote:
            stats = pacote["stats_atuais"]
            try:
                print("  -> stats_atuais vazio?", stats is None or getattr(stats, "empty", False))
                if hasattr(stats, "head"):
                    print("  -> stats_atuais index (até 20):", list(stats.index)[:20])
                    print(stats.head(3).to_string())
            except Exception as e:
                print("  -> Não foi possível inspecionar stats_atuais:", e)
    except Exception as e:
        print("  ❌ Erro ao carregar pickle:", e)
        traceback.print_exc()

def main():
    list_files()

    # nomes usados pelo seu script
    csvs = [
        "data/base_com_features_ENRICHED.csv",
        "data/base_com_features_FINAL.csv",
        "data/base_com_features.csv"
    ]
    for c in csvs:
        check_csv(c)

    # checar o arquivo de saída
    check_pickle("data/sistema_nba_v1.pkl")

    # imprimir versão do python e pacotes mínimos
    print("\n➡️  AMBIENTE")
    print(" Python:", sys.version.replace("\n", " "))
    try:
        import pandas as pd; import numpy as np; import statsmodels
        print(" pandas:", pd.__version__, " numpy:", np.__version__, " statsmodels:", statsmodels.__version__)
    except Exception as e:
        print(" Erro ao checar versões de pacotes:", e)

if __name__ == "__main__":
    main()
