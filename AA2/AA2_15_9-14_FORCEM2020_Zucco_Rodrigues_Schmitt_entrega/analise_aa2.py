"""OPIA / AA2: análise reproduzível de um LAS público, baseada na Aula 3.

Execute: python analise_aa2.py
Os parâmetros estão em config.json. Nenhum dado bruto é sobrescrito.
"""
from pathlib import Path
import argparse
import hashlib
import html
import json
import os

BASE = Path(__file__).resolve().parent
os.environ.setdefault("MPLCONFIGDIR", str(BASE / ".cache" / "matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import lasio

PRINCIPAIS = ["GR", "RT", "NPHI", "RHOB"]
LITOLOGIAS = {30000: "Arenito", 65030: "Arenito/folhelho", 65000: "Folhelho",
    80000: "Marga", 74000: "Dolomito", 70000: "Calcário", 70032: "Giz calcário",
    88000: "Halita", 86000: "Anidrita", 99000: "Tufo", 90000: "Carvão", 93000: "Embasamento"}
FONTES = {
    "chave_litologica": "https://thinkonward.com/app/c/challenges/force-well-logs",
    "dataset": "https://zenodo.org/records/4351156",
    "doi": "https://doi.org/10.5281/zenodo.4351156",
    "repositorio": "https://github.com/bolgebrygg/Force-2020-Machine-Learning-competition",
    "aula3": "Eduardo Paiva (UDESC), Aula 3 — Manipulação de dados",
    "archie": "https://glossary.slb.com/en/terms/a/archie_equation",
}


def carregar_config(caminho=None):
    caminho = Path(caminho) if caminho else BASE / "config.json"
    cfg = json.loads(caminho.read_text(encoding="utf-8"))
    if cfg["gr_folhelho_api"] <= cfg["gr_limpo_api"]:
        raise ValueError("GR de folhelho deve ser maior que GR limpo.")
    for k in ["rw_ohm_m", "archie_a", "archie_m", "archie_n", "intervalo_min_m"]:
        if not np.isfinite(cfg[k]) or cfg[k] <= 0:
            raise ValueError(f"{k} deve ser positivo e finito.")
    for k in ["phi_min", "sw_max", "vcl_max"]:
        if not 0 < cfg[k] < 1:
            raise ValueError(f"{k} deve estar entre 0 e 1.")
    if cfg["interpolar_lacuna_max_m"] < 0:
        raise ValueError("O limite de interpolação não pode ser negativo.")
    if cfg["rho_matriz_g_cm3"] <= cfg["rho_fluido_g_cm3"]:
        raise ValueError("Densidade da matriz deve superar a do fluido.")
    return cfg


def carregar_las(caminho, cfg):
    """Lê o NULL declarado no LAS e valida unidades antes de calcular."""
    caminho = Path(caminho)
    las = lasio.read(caminho, null_policy="strict")
    original = las.df()
    original.index.name = "PROFUNDIDADE_M"
    z = original.index.to_numpy(dtype=float)
    if not np.isfinite(z).all() or pd.Index(z).has_duplicates:
        raise ValueError("Profundidade inválida ou duplicada: revisar o LAS.")
    original = original.sort_index()
    unidade_z = las.curves[0].unit.lower().strip()
    if unidade_z not in {"m", "meter", "metre"}:
        raise ValueError(f"Este projeto exige profundidade em metros; recebida {unidade_z}.")
    unidades = {c.mnemonic: c.unit.lower().strip() for c in las.curves}
    aceitas = {"GR": {"gapi", "api"}, "RT": {"ohm.m", "ohmm", "ohm-m"},
               "NPHI": {"m3/m3", "v/v", "frac", "%", "pu"},
               "RHOB": {"g/cm3", "g/c3", "g/cc", "kg/m3"}}
    dados = pd.DataFrame(index=original.index)
    for destino, origem in cfg["curvas"].items():
        if origem not in original:
            raise ValueError(f"Curva {origem} ausente. Ajuste config.json.")
        if unidades[origem] not in aceitas[destino]:
            raise ValueError(f"Conferir unidade de {origem}: {unidades[origem]}")
        dados[destino] = pd.to_numeric(original[origem], errors="coerce")
        if destino == "NPHI" and unidades[origem] in {"%", "pu"}:
            dados[destino] /= 100
        if destino == "RHOB" and unidades[origem] == "kg/m3":
            dados[destino] /= 1000
    # Mantém códigos geológicos de referência, sem inventar uma litologia por GR.
    for c in original:
        if "LITHOLOGY" in c:
            dados["LITOLOGIA_CODIGO_FORCE"] = original[c]
        if "CONFIDENCE" in c:
            dados["CONFIANCA_FORCE"] = original[c]
    if "LITOLOGIA_CODIGO_FORCE" in dados:
        dados["LITOLOGIA_REFERENCIA"] = dados.LITOLOGIA_CODIGO_FORCE.map(LITOLOGIAS).fillna("Não identificada")
    curvas = pd.DataFrame([{"curva": c.mnemonic, "unidade": c.unit,
                            "descricao": c.descr} for c in las.curves])
    meta = {"poco": str(las.well.WELL.value).strip(), "arquivo": caminho.name,
            "sha256": hashlib.sha256(caminho.read_bytes()).hexdigest(),
            "amostras": len(dados), "profundidade_min_m": float(dados.index.min()),
            "profundidade_max_m": float(dados.index.max()),
            "passo_mediano_m": float(np.median(np.diff(dados.index))),
            "passo_cabecalho_m": float(las.well.STEP.value),
            "null_declarado": float(las.well.NULL.value),
            "fontes": FONTES, "licenca_registro": "CC BY 4.0; origem NOLD 2.0, conforme Zenodo"}
    return original, dados, curvas, meta


def interpolar_lacunas_curtas(serie, max_m):
    """Preenche somente lacunas internas inteiras, limitadas pela distância
    entre seus dois pontos válidos. Não extrapola nem preenche parte de lacuna longa.
    """
    out = serie.copy()
    z = serie.index.to_numpy(float)
    a = serie.to_numpy(float)
    missing = ~np.isfinite(a)
    starts = np.flatnonzero(missing & ~np.r_[False, missing[:-1]])
    ends = np.flatnonzero(missing & ~np.r_[missing[1:], False])
    for start, end in zip(starts, ends):
        if start == 0 or end == len(a) - 1:
            continue
        if z[end + 1] - z[start - 1] <= max_m + 1e-9:
            out.iloc[start:end + 1] = np.interp(z[start:end + 1],
                [z[start - 1], z[end + 1]], [a[start - 1], a[end + 1]])
    return out


def limpar_dados(dados, cfg):
    """Conserva a malha original. IQR sinaliza; limites físicos amplos invalidam."""
    limpo = dados.copy()
    flags = pd.DataFrame(index=dados.index)
    linhas = []
    limites = {"GR": (0, np.inf), "RT": (0, np.inf),
               "NPHI": (-0.15, 1.0), "RHOB": (1.0, 4.0)}
    for c in PRINCIPAIS:
        s = dados[c].replace([np.inf, -np.inf], np.nan)
        lo, hi = limites[c]
        fisico = (s < lo) | (s > hi) | ((s == 0) if c == "RT" else False)
        valido = s.mask(fisico)
        # RT é analisada em log10 devido à distribuição assimétrica.
        qserie = np.log10(valido) if c == "RT" else valido
        q1, q3 = qserie.quantile([0.25, 0.75])
        iqr = q3 - q1
        extremo = ((qserie < q1 - 1.5 * iqr) | (qserie > q3 + 1.5 * iqr))
        preenchido = interpolar_lacunas_curtas(valido, cfg["interpolar_lacuna_max_m"])
        flags[c + "_AUSENTE_ORIGINAL"] = s.isna()
        flags[c + "_INVALIDO_FISICO"] = fisico
        flags[c + "_EXTREMO_IQR"] = extremo
        flags[c + "_INTERPOLADO"] = valido.isna() & preenchido.notna()
        limpo[c] = preenchido
        linhas.append({"curva": c, "ausentes_antes": int(s.isna().sum()),
                       "invalidos_fisicos": int(fisico.sum()),
                       "extremos_iqr_sinalizados": int(extremo.sum()),
                       "interpolados": int(flags[c + "_INTERPOLADO"].sum()),
                       "ausentes_depois": int(preenchido.isna().sum())})
    return limpo, flags, pd.DataFrame(linhas)


def calcular_atributos(limpo, cfg):
    """PHIE segue a rotina apresentada na Aula 3: NPHI*(1-VCL)."""
    df = limpo.copy()
    df["VCL"] = ((df.GR - cfg["gr_limpo_api"]) /
                 (cfg["gr_folhelho_api"] - cfg["gr_limpo_api"])).clip(0, 1)
    phi = df.NPHI * (1 - df.VCL)
    df["PHIE"] = phi.where(phi.between(0, 1))
    df["PHID"] = ((cfg["rho_matriz_g_cm3"] - df.RHOB) /
                   (cfg["rho_matriz_g_cm3"] - cfg["rho_fluido_g_cm3"]))
    df["PHI_ND_EXEMPLO_SLIDE"] = (df.NPHI + df.PHID) / 2
    valido = (df.PHIE > 0) & (df.RT > 0)
    df["SW_ARCHIE_BRUTA"] = np.nan
    df.loc[valido, "SW_ARCHIE_BRUTA"] = (
        cfg["archie_a"] * cfg["rw_ohm_m"] /
        (df.loc[valido, "PHIE"] ** cfg["archie_m"] * df.loc[valido, "RT"])
    ) ** (1 / cfg["archie_n"])
    df["SW"] = df.SW_ARCHIE_BRUTA.clip(0, 1)
    df["SW_ACIMA_1"] = df.SW_ARCHIE_BRUTA > 1
    df["SH"] = 1 - df.SW
    df["BVW"] = df.PHIE * df.SW
    df["AVALIAVEL"] = df[["GR", "RT", "NPHI", "RHOB", "PHIE", "SW"]].notna().all(axis=1)
    df["POTENCIAL"] = (df.AVALIAVEL & (df.PHIE > cfg["phi_min"]) &
                         (df.SW < cfg["sw_max"]) & (df.VCL < cfg["vcl_max"]))
    df["CLASSE"] = np.select([~df.AVALIAVEL, df.POTENCIAL],
        ["Sem dados suficientes", "Potencial pelos critérios"], default="Fora dos critérios")
    return df


def suporte_profundidade(index):
    """Células de profundidade por pontos médios, truncadas em min/max.
    Não conta grandes saltos como rocha amostrada.
    """
    z = np.asarray(index, dtype=float)
    if len(z) < 2 or np.any(np.diff(z) <= 0):
        raise ValueError("São necessárias pelo menos duas profundidades crescentes.")
    gap = np.diff(z)
    step = np.median(gap)
    meia = np.where(gap <= 1.5 * step, gap / 2, 0.0)
    left = z - np.r_[0., meia]
    right = z + np.r_[meia, 0.]
    return left, right, right - left, step


def resumir_intervalos(df, cfg):
    left, right, pesos, step = suporte_profundidade(df.index)
    mask = df.POTENCIAL.to_numpy(bool)
    z = df.index.to_numpy(float)
    rows = []
    inicio = None
    for i in range(len(df)):
        if inicio is not None and (not mask[i] or z[i] - z[i-1] > 1.5 * step):
            rows.append((inicio, i - 1)); inicio = None
        if mask[i] and inicio is None:
            inicio = i
    if inicio is not None:
        rows.append((inicio, len(df) - 1))
    result = []
    for a, b in rows:
        sub = df.iloc[a:b+1]
        if pesos[a:b+1].sum() == 0:
            continue
        result.append({"topo_m": left[a], "base_m": right[b],
            "espessura_md_m": float(pesos[a:b+1].sum()), "amostras": b-a+1,
            "phie_media": float(np.average(sub.PHIE, weights=pesos[a:b+1])),
            "sw_media": float(np.average(sub.SW, weights=pesos[a:b+1])),
            "vcl_media": float(np.average(sub.VCL, weights=pesos[a:b+1]))})
    col = ["topo_m", "base_m", "espessura_md_m", "amostras", "phie_media", "sw_media", "vcl_media"]
    intervalos = pd.DataFrame(result, columns=col)
    intervalos["atinge_espessura_minima"] = intervalos.espessura_md_m >= cfg["intervalo_min_m"]
    return intervalos.sort_values("espessura_md_m", ascending=False).reset_index(drop=True)


def resumo_numerico(df, intervalos):
    _, _, w, _ = suporte_profundidade(df.index)
    avaliavel = df.AVALIAVEL.to_numpy(bool)
    potencial = df.POTENCIAL.to_numpy(bool)
    aval_m = float(w[avaliavel].sum())
    pot_m = float(w[potencial].sum())
    return {"amostras": len(df), "amostras_avaliaveis": int(avaliavel.sum()),
            "amostras_potenciais": int(potencial.sum()),
            "extensao_amostrada_md_m": float(w.sum()),
            "extensao_avaliavel_md_m": aval_m,
            "espessura_potencial_md_m": pot_m,
            "fracao_potencial_sobre_avaliavel": pot_m / aval_m if aval_m else None,
            "intervalos_potenciais": len(intervalos),
            "intervalos_com_espessura_minima": int(intervalos.atinge_espessura_minima.sum()),
            "amostras_potenciais_carvao": int((df.POTENCIAL &
                df.get("LITOLOGIA_CODIGO_FORCE", pd.Series(np.nan,index=df.index)).eq(90000)).sum()),
            "sw_bruta_acima_1": int(df.SW_ACIMA_1.sum())}


def sensibilidade(limpo, cfg):
    rows = []
    for rw in [0.05, 0.1, 0.2]:
        c = dict(cfg, rw_ohm_m=rw)
        d = calcular_atributos(limpo, c)
        r = resumo_numerico(d, resumir_intervalos(d, c))
        rows.append({"rw_ohm_m": rw, "espessura_potencial_md_m": r["espessura_potencial_md_m"],
                     "fracao_potencial_sobre_avaliavel": r["fracao_potencial_sobre_avaliavel"]})
    return pd.DataFrame(rows)


def gerar_graficos(bruto, df, auditoria, intervalos, pasta, meta):
    pasta.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", font_scale=0.95)
    paths = []
    def salvar(fig, nome):
        fig.savefig(pasta / nome, dpi=160, bbox_inches="tight")
        plt.close(fig); paths.append(pasta / nome)
    z = df.index
    fig, ax = plt.subplots(1, 5, figsize=(14, 10), sharey=True, layout="constrained")
    fig.suptitle(f"Poço {meta['poco']} | perfis e estimativas didáticas", fontsize=16, weight="bold")
    ax[0].plot(df.GR, z, color="#25844d", lw=.65); ax[0].set_xlabel("GR (API)")
    ax[1].semilogx(df.RT, z, color="#b14a35", lw=.65); ax[1].set_xlabel("RDEP (ohm.m)")
    ax[2].plot(df.NPHI, z, color="#235caa", lw=.65); ax[2].set_xlabel("NPHI (fração)")
    twin = ax[2].twiny(); twin.plot(df.RHOB,z,color="#b14a35",lw=.6,alpha=.7)
    twin.set_xlabel("RHOB (g/cm³)",color="#b14a35")
    ax[3].plot(df.PHIE,z,label="PHIE",color="#7b3fa1",lw=.7)
    ax[3].plot(df.SW,z,label="Sw",color="#129dad",lw=.7)
    ax[3].set_xlabel("Fração"); ax[3].legend(loc="best")
    left,right,_,_=suporte_profundidade(z)
    # Cada faixa corresponde a um intervalo contíguo; lacunas não são unidas.
    ax[4].fill_betweenx(z,0,1,where=~df.AVALIAVEL,color="#b8bec7",step="mid",label="Sem avaliação")
    for _, row in intervalos.iterrows():
        ax[4].axhspan(row.topo_m,row.base_m,color="#d89b24",alpha=.85)
    ax[4].set_xlim(0,1); ax[4].set_xticks([]); ax[4].set_xlabel("Dourado: potencial\nCinza: sem avaliação")
    ax[0].set_ylabel("Profundidade medida (m)"); ax[0].set_ylim(z.max(),z.min())
    salvar(fig,"01_perfis.png")
    fig, axes=plt.subplots(2,2,figsize=(11,7),layout="constrained")
    fig.suptitle("Distribuições antes e depois do tratamento",weight="bold")
    for a,c in zip(axes.flat,PRINCIPAIS):
        x=bruto[c].dropna(); y=df[c].dropna()
        if c=="RT": x=np.log10(x[x>0]);y=np.log10(y[y>0])
        bins=np.histogram_bin_edges(pd.concat([x,y]),bins=45)
        a.hist(x,bins=bins,histtype="step",color="#718096",label="Original")
        a.hist(y,bins=bins,histtype="step",color="#245faa",label="Tratado")
        a.set_xlabel("log10 RT" if c=="RT" else c);a.set_ylabel("Amostras");a.legend()
    salvar(fig,"02_distribuicoes.png")
    fig,axes=plt.subplots(1,2,figsize=(13,5),layout="constrained")
    c=["GR","RT","NPHI","RHOB","PHIE","VCL","SW"]
    sns.heatmap(df[c].corr(),annot=True,fmt=".2f",vmin=-1,vmax=1,center=0,cmap="vlag",ax=axes[0])
    axes[0].set_title("Pearson: pares disponíveis\nVariáveis derivadas têm dependência matemática")
    d=df.loc[df.AVALIAVEL]
    p=axes[1].scatter(d.PHIE,d.SW,c=d.VCL,s=4,alpha=.5,cmap="viridis",rasterized=True)
    axes[1].set(xlabel="PHIE (fração)",ylabel="Sw (fração)",title="Estimativas pelo modelo da aula")
    fig.colorbar(p,ax=axes[1],label="VCL (fração)")
    salvar(fig,"03_correlacoes.png")
    fig,ax=plt.subplots(figsize=(9,4),layout="constrained")
    a=auditoria.set_index("curva")[["ausentes_antes","ausentes_depois"]]
    a.plot.bar(ax=ax,color=["#9da9b8","#235caa"],rot=0)
    ax.set(title="Lacunas: somente trechos internos curtos são preenchidos",ylabel="Amostras",xlabel="Curva")
    ax.legend(["Antes","Depois"]);salvar(fig,"04_qualidade.png")
    return paths


def gerar_relatorio(meta, cfg, resumo, auditoria, intervalos, sens, pasta):
    """Relatório HTML portátil: figuras relativas e números obtidos da execução."""
    r=resumo
    pct=r['fracao_potencial_sobre_avaliavel']
    pct_txt=f"{100*pct:.2f}%" if pct is not None else "não calculável"
    melhores=intervalos.loc[intervalos.atinge_espessura_minima].head(10)
    todos_min=intervalos.loc[intervalos.atinge_espessura_minima]
    faixa_min=(f"Os intervalos que atingem a espessura mínima estão entre "
               f"{todos_min.topo_m.min():.3f} e {todos_min.base_m.max():.3f} m MD, "
               "em trechos separados, conforme a tabela." if len(todos_min) else
               "Nenhum intervalo atinge a espessura mínima configurada.")
    tabelas=lambda df: df.to_html(index=False,float_format=lambda x:f"{x:.4f}",border=0)
    texto=f'''# OPIA — Atividade Avaliativa 2

## Análise do poço {meta['poco']} — FORCE 2020

Arquivo: **{meta['arquivo']}**. Integrantes: **Leandro Alex Zucco; Gustavo Mendes Rodrigues; Jair Antonio Schmitt Junior**.

## Resultado

Foram lidas {r['amostras']:,} amostras, entre {meta['profundidade_min_m']:.3f} e
{meta['profundidade_max_m']:.3f} m de profundidade medida (MD).
Após tratamento, {r['amostras_avaliaveis']:,} amostras permitem avaliar os critérios.
A soma dos trechos que atendem aos cortes é **{r['espessura_potencial_md_m']:.3f} m MD**,
ou **{pct_txt}** da extensão avaliável de {r['extensao_avaliavel_md_m']:.3f} m MD.
Foram encontrados {r['intervalos_potenciais']} intervalos contíguos;
{r['intervalos_com_espessura_minima']} atingem {cfg['intervalo_min_m']} m MD.
Essas espessuras são comprimentos ao longo do poço; não são espessuras verticais verdadeiras.

## Dados e método

Fonte: {FONTES['doi']}. Documentação: {FONTES['repositorio']}.
O registro descreve dados já parcialmente limpos e despiculados; nosso “original” é o LAS
distribuído pelo FORCE, não o registro instrumental primário.
Licenças informadas no registro: CC BY 4.0 e origem sob NOLD 2.0.
SHA-256: {meta['sha256']}.
RDEP foi associado a RT. Unidades verificadas no cabeçalho: profundidade em m,
GR em gAPI, RDEP em ohm.m, NPHI em m3/m3 e RHOB em g/cm3.

O valor NULL é convertido em ausente. A malha de profundidade é preservada.
Limites físicos de triagem: GR >= 0; RT > 0; -0,15 <= NPHI <= 1; 1 <= RHOB <= 4.
Esses limites são amplos e não substituem controle instrumental.
O método IQR sinaliza extremos (log10 para RT), sem excluí-los automaticamente.
Só são interpoladas lacunas internas cuja distância entre os pontos válidos vizinhos
seja no máximo {cfg['interpolar_lacuna_max_m']} m. Não se extrapolam as extremidades.

## Equações e hipóteses

VCL = clip((GR - {cfg['gr_limpo_api']}) / ({cfg['gr_folhelho_api']} - {cfg['gr_limpo_api']}), 0, 1).
PHIE = NPHI × (1 - VCL), seguindo a rotina apresentada na Aula 3; resultados fora de [0,1] ficam ausentes.
Sw_bruta = [a × Rw / (PHIE^m × RT)]^(1/n), com a={cfg['archie_a']},
m={cfg['archie_m']}, n={cfg['archie_n']} e Rw={cfg['rw_ohm_m']} ohm.m.
Sw é limitada a [0,1], mantendo Sw_bruta e uma indicação dos {r['sw_bruta_acima_1']} valores acima de 1.
Porosidade zero ou negativa não recebe valor artificial para calcular Archie.
SH = 1 - Sw; BVW = PHIE × Sw.

O exemplo alternativo do slide é exportado separadamente:
PHID = (rho_matriz - RHOB)/(rho_matriz - rho_fluido);
PHI_ND_EXEMPLO_SLIDE = (NPHI + PHID)/2.
Ele não é usado para selecionar intervalos. Não se misturam as duas estimativas.

Cortes de seleção: PHIE > {cfg['phi_min']}; Sw < {cfg['sw_max']}; VCL < {cfg['vcl_max']}.
São hipóteses didáticas, não valores calibrados para este poço.
Todas as quatro curvas devem estar disponíveis para a avaliação.
Cada amostra representa uma célula delimitada pelos pontos médios vizinhos,
truncada no início/fim do registro. Saltos maiores que 1,5 vezes o passo mediano quebram
intervalos e não recebem espessura. O denominador da fração potencial contém somente
células avaliáveis. Intervalos menores que o mínimo continuam no total e são identificados na tabela.

## Interpretação geológica e limites

Nesta execução, **{r['amostras_potenciais_carvao']} das {r['amostras_potenciais']} amostras selecionadas**
estão classificadas como carvão (código 90000) no próprio FORCE.
Portanto, os {r['espessura_potencial_md_m']:.3f} m são somente o resultado bruto dos cortes didáticos,
não uma estimativa validada de espessura produtora de petróleo.
A comparação litológica está em `comparacao_litologica.csv`.
{faixa_min}
As porosidades estimadas elevadas nesses trechos devem motivar revisão de litologia e resposta instrumental.

Os trechos selecionados apresentam, segundo as hipóteses adotadas, menor resposta relativa
de GR, porosidade estimada suficiente e resposta de resistividade compatível com Sw menor.
Isso indica candidatos a investigação petrofísica; não comprova hidrocarbonetos nem produtividade.
GR isolado não determina litologia: minerais radioativos e a composição da formação afetam o sinal.
Os códigos litológicos fornecidos no LAS foram preservados como referência e não gerados por cortes de GR.
PHIE baseada apenas em NPHI e GR é uma aproximação; matriz, argila e fluidos podem alterar as respostas.
Archie é uma aproximação para rochas limpas; argila condutiva limita sua aplicação.
Rw e parâmetros de Archie precisam de calibração, e a análise de sensibilidade mostra seu impacto.
Correlações envolvendo PHIE, VCL e Sw refletem também as próprias fórmulas e não comprovam causalidade.
Não há treinamento de aprendizado de máquina: esta atividade prepara e interpreta os dados.

## Recomendações técnicas

Revisar os maiores intervalos na tabela junto a CALI, DRHO e demais curvas originais.
Conferir litologia de referência, efeitos de argila/gás e condições de poço.
Calibrar extremos de GR, Rw e parâmetros de Archie com informações independentes.
Comparar intervalos com e sem amostras interpoladas antes de qualquer decisão operacional.

## Referências

- Dataset e licenças: {FONTES['doi']}
- Documentação FORCE: {FONTES['repositorio']}
- Chave de códigos litológicos e confiança: {FONTES['chave_litologica']}
- Eduardo Paiva, UDESC, Aula 3, slides e rotinas: {FONTES['aula3']}
- Equação de Archie e contexto: {FONTES['archie']}
'''
    (pasta/"relatorio.md").write_text(texto,encoding="utf-8")
    # Conversão mínima e explícita para HTML; todo o texto é escapado.
    sections=[]
    for block in texto.split("\n\n"):
        if block.startswith("## "): sections.append("<h2>"+html.escape(block[3:])+"</h2>")
        elif block.startswith("# "): sections.append("<h1>"+html.escape(block[2:])+"</h1>")
        else: sections.append("<p>"+html.escape(block).replace("\n"," ").replace("**","")+"</p>")
    tables="<h2>Auditoria da limpeza</h2>"+tabelas(auditoria)
    tables+="<h2>Maiores intervalos com espessura mínima</h2>"+tabelas(melhores)
    tables+="<h2>Sensibilidade a Rw</h2>"+tabelas(sens)
    figures=''.join(f'<figure><img src="figuras/{n}" alt="{n}"></figure>' for n in
        ["01_perfis.png","02_distribuicoes.png","03_correlacoes.png","04_qualidade.png"])
    doc='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>OPIA AA2 — Poço 15/9-14</title>
<style>body{font:17px/1.6 system-ui,sans-serif;max-width:1080px;margin:40px auto;padding:0 24px;color:#203047}
h1,h2{color:#124776}h1{font-size:34px}h2{margin-top:36px}table{border-collapse:collapse;width:100%;font-size:13px}
td,th{padding:9px;border-bottom:1px solid #ccd7e1;text-align:right}th{background:#edf3f8}
img{width:100%;height:auto}figure{margin:35px 0}p{overflow-wrap:anywhere}@media print{body{font-size:11px}figure{break-inside:avoid}}</style><body>'''
    (pasta/"relatorio.html").write_text(doc+''.join(sections)+tables+figures+"</body></html>",encoding="utf-8")


def executar(config_path=None, saida=None):
    cfg=carregar_config(config_path)
    pasta=Path(saida) if saida else BASE/"resultados"
    pasta.mkdir(parents=True,exist_ok=True)
    caminho=Path(cfg["arquivo_las"])
    if not caminho.is_absolute(): caminho=BASE/caminho
    original,bruto,curvas,meta=carregar_las(caminho,cfg)
    limpo,flags,auditoria=limpar_dados(bruto,cfg)
    df=calcular_atributos(limpo,cfg)
    intervalos=resumir_intervalos(df,cfg)
    resumo=resumo_numerico(df,intervalos)
    sens=sensibilidade(limpo,cfg)
    if "LITOLOGIA_REFERENCIA" in df:
        df.groupby("LITOLOGIA_REFERENCIA")[PRINCIPAIS+["PHIE","SW"]].agg(
            ["count","mean","std","min","max"]).to_csv(pasta/"estatisticas_por_litologia.csv")
        comparacao = df.loc[df.POTENCIAL].groupby("LITOLOGIA_REFERENCIA",dropna=False).agg(
            amostras=("POTENCIAL","size"), nphi_media=("NPHI","mean"),
            rhob_media=("RHOB","mean"), rt_media=("RT","mean"))
        comparacao.to_csv(pasta/"comparacao_litologica.csv")
    for nome,tabela,indice in [
        ("dados_processados.csv",df,True),("sinalizadores_qualidade.csv",flags,True),
        ("auditoria_limpeza.csv",auditoria,False),("intervalos_potenciais.csv",intervalos,False),
        ("curvas_disponiveis.csv",curvas,False),("sensibilidade_rw.csv",sens,False),
        ("estatisticas.csv",df[PRINCIPAIS+["PHIE","VCL","SW"]].describe(),True)]:
        tabela.to_csv(pasta/nome,index=indice)
    (pasta/"resumo.json").write_text(json.dumps({"metadados":meta,"parametros":cfg,"resultados":resumo},
        indent=2,ensure_ascii=False,allow_nan=False),encoding="utf-8")
    graficos=gerar_graficos(bruto,df,auditoria,intervalos,pasta/"figuras",meta)
    gerar_relatorio(meta,cfg,resumo,auditoria,intervalos,sens,pasta)
    return {"dados":df,"bruto":bruto,"limpo":limpo,"flags":flags,"auditoria":auditoria,
            "intervalos":intervalos,"resumo":resumo,"metadados":meta,"graficos":graficos,"sensibilidade":sens}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config",type=Path)
    parser.add_argument("--saida",type=Path)
    args=parser.parse_args()
    resultado=executar(args.config,args.saida)
    print(json.dumps(resultado["resumo"],indent=2,ensure_ascii=False))
    print("Análise concluída. Consulte resultados/relatorio.html.")
