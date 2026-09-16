# OPIA — Atividade Avaliativa 2

Análise local de perfis de poço do arquivo `dados/15_9-14.las`, do conjunto FORCE 2020 (Zenodo 4351156).

## Execução no VS Code

Recomenda-se Python 3.13. No terminal, dentro desta pasta:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

No VS Code, selecione o interpretador `.venv/bin/python` em **Python: Select Interpreter**. No Windows, use `.venv\\Scripts\\activate`.

O programa localiza o LAS por meio de `config.json`, usando o caminho relativo `dados/15_9-14.las`. Para trocar o poço, altere esse parâmetro e o mapeamento das curvas.

## Saídas

`main.py` chama as funções de `analise_aa2.py`. A execução recria `resultados/`, incluindo `relatorio.html`, `relatorio.md`, `resumo.json`, quatro gráficos em `figuras/` e tabelas CSV de dados tratados, auditoria, intervalos, estatísticas, litologia e sensibilidade de Rw.

As curvas são verificadas no cabeçalho do LAS. O tratamento converte o NULL declarado em ausente, sinaliza extremos por IQR, interpola somente lacunas internas curtas e preserva a profundidade medida. PHIE, VCL e Archie seguem as hipóteses explicitadas no relatório; os códigos litológicos fornecidos pelo FORCE são preservados.

## Identificação

Integrantes: Leandro Alex Zucco; Gustavo Mendes Rodrigues; Jair Antonio Schmitt Junior.

Fonte: https://doi.org/10.5281/zenodo.4351156. A escolha do arquivo deve ser conferida no Moodle para evitar repetição entre grupos.

O código foi adaptado das rotinas da Aula 3 de Eduardo Paiva (UDESC), sem depender de Colab, Jupyter ou IPython.
