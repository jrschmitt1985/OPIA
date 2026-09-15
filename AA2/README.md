# OPIA — Atividade Avaliativa 2

## Comece aqui

Abra esta pasta no VS Code e abra **AA2_analise.ipynb**. No canto superior direito,
escolha o ambiente Python **.venv** desta pasta. Execute as células em ordem.
O notebook já inclui uma execução salva e explicações em português.

Para rodar como programa, use o terminal do VS Code, dentro da pasta AA2:

```sh
source .venv/bin/activate
python analise_aa2.py
```

Abra **resultados/relatorio.html** no navegador para ler o relatório e os gráficos.
Mantenha a pasta `figuras` junto do HTML para as imagens aparecerem.

## Poço escolhido

- Arquivo original: **dados/15_9-14.las**
- Identificador: **15/9-14**
- Origem: **FORCE 2020 / Zenodo**, https://doi.org/10.5281/zenodo.4351156
- Sugestão de descrição do grupo: **AA2 — 15_9-14.las — FORCE 2020 (Zenodo 4351156)**
- Integrantes: Leandro Alex Zucco; Gustavo Mendes Rodrigues; Jair Antonio Schmitt Junior.
- Conferir no Moodle se outro grupo já escolheu esse arquivo.
- Prazo informado: **16/09/2026, 14h**. Trabalho permitido em trios.

O LAS escolhido foi extraído de uma entrada completa do ZIP oficial, validada pelo
CRC-32 registrado no ZIP. O pacote completo não integra o projeto.
O SHA-256 do LAS está em `resultados/resumo.json` e no relatório.
O registro oficial e suas informações de licença estão salvos em
`referencias/zenodo_4351156.json`. O registro indica CC BY 4.0 e dados originais sob NOLD 2.0.
Documentação: https://github.com/bolgebrygg/Force-2020-Machine-Learning-competition

## Organização

- `analise_aa2.py`: leitura, limpeza, cálculos, intervalos, gráficos e exportações.
- `config.json`: arquivo, mapeamento das curvas, parâmetros e cortes editáveis.
- `AA2_analise.ipynb`: sequência didática comentada para estudo e entrega.
- `dados/`: LAS real preservado.
- `referencias/`: notebooks originais do professor e metadados da fonte.
- `resultados/`: relatório, figuras, dados tratados, auditoria, intervalos e sensibilidade.
- `test_analise.py`: verificações de lacunas, intervalos e casos matemáticos conhecidos.
- `.venv/`: ambiente Python instalado localmente; não enviar na entrega.

## O que foi adaptado da aula

As rotinas originais estão copiadas integralmente como referência; o programa é uma
adaptação comentada, com as seguintes mudanças:

1. `RDEP` do LAS corresponde a `RT` no Colab. As unidades são verificadas antes dos cálculos.
2. O NULL declarado no arquivo é tratado pelo lasio. Profundidade é preservada nas exportações.
3. Lacunas longas e extremidades ficam ausentes; só pequenas lacunas internas são interpoladas.
4. IQR sinaliza extremos em vez de apagá-los automaticamente. RT usa log10 para essa triagem.
5. PHIE segue o Colab, `NPHI*(1-VCL)`. A fórmula do slide baseada em densidade é exportada
   como comparação separada, sem substituir a PHIE usada na seleção.
6. Archie não recebe porosidade positiva inventada. A saturação antes do limite [0,1] fica disponível.
7. Trechos contíguos são separados de verdade; a extensão usa a profundidade medida real,
   sem assumir passo de 0,5 m. O passo do arquivo é aproximadamente 0,152 m.
8. Rw e cortes são hipóteses didáticas, explicitadas no relatório. Há comparação com Rw=0,05/0,10/0,20.
9. Os códigos de litologia existentes são preservados. Não se inventa litologia a partir de GR.

Essas estimativas apontam potencial pelos critérios adotados, não produtividade confirmada.
Não há modelo de aprendizado de máquina nesta etapa de preparação e interpretação dos dados.

## Recriar o ambiente em outro computador

Use Python 3.13 para reproduzir o ambiente testado:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python analise_aa2.py
python -m unittest -v test_analise.py
```

No Windows, a ativação no PowerShell é `.venv\Scripts\Activate.ps1`.
Caso as extensões Python/Jupyter não estejam instaladas no VS Code, o programa `.py`
pode ser executado pelo terminal. O notebook precisa de suporte a Jupyter no editor.

## Antes de entregar

Revise o relatório e as hipóteses, preencha os integrantes na primeira célula do notebook,
confirme a exclusividade do LAS no Moodle e confira o formato aceito para envio.
O pacote contém notebook, programa, parâmetros, LAS e resultados; `.venv` e caches não são necessários.
Nenhum registro de grupo ou envio ao Moodle foi realizado automaticamente.
