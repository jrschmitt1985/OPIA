"""Ponto de entrada da Atividade Avaliativa 2: python main.py."""
import json
from analise_aa2 import executar

if __name__ == "__main__":
    resultado = executar()
    print(json.dumps(resultado["resumo"], indent=2, ensure_ascii=False))
    print("Análise concluída. Consulte a pasta resultados.")
