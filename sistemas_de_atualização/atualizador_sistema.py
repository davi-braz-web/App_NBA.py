import subprocess
import sys
import os
import time

def run_script(script_name):
    """Executa um script python e aguarda a finalização."""
    if os.path.exists(script_name):
        print(f"🚀 Iniciando: {script_name}...")
        try:
            subprocess.run([sys.executable, script_name], check=True)
            print(f"✅ {script_name} concluído com sucesso.\n")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao executar {script_name}: {e}")
            return False
    else:
        print(f"⚠️ Aviso: Arquivo {script_name} não encontrado.")
        return False

def main():
    start_time = time.time()
    print(f"--- INICIANDO ATUALIZAÇÃO DO SISTEMA NBA SNIPER ({time.ctime()}) ---\n")

    pipeline = [
        "update_system.py",      # 1/5: Estatísticas
        "update_injuries.py",    # 2/5: Lesões
        "update_news.py",        # 3/5: Newsletter
        "deploy_modelo_final.py",# 4/5: Re-treinamento
        "previsao_diaria.py"     # 5/5: Previsões do dia
    ]

    for script in pipeline:
        success = run_script(script)
        if not success and script == "update_system.py":
            print("🛑 Falha crítica no primeiro passo. Abortando pipeline.")
            sys.exit(1)

    duration = (time.time() - start_time) / 60
    print(f"--- PIPELINE FINALIZADO COM SUCESSO EM {duration:.2f} MINUTOS ---")

if __name__ == "__main__":
    main()