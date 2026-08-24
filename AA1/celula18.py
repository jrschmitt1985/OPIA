# ============================================================================
# CÉLULA 18: ATIVIDADE AVALIATIVA - PREVISÃO DE PRODUÇÃO DE POÇOS
# ============================================================================

import numpy as np
import pandas as pd

# 1. Geração de Dados Sintéticos Realistas
np.random.seed(123)
n_pocos = 50

# Variáveis independentes (features)
phi = np.random.uniform(0.08, 0.25, n_pocos)      # Porosidade (8-25%)
k = np.random.lognormal(3, 1, n_pocos)            # Permeabilidade (log-normal)
k = np.clip(k, 10, 1000)                          # Clip entre 10-1000 mD
h = np.random.uniform(10, 50, n_pocos)            # Espessura (10-50 m)
p = np.random.uniform(200, 400, n_pocos)          # Pressão (200-400 psi)

# Variável dependente (target) - Produção
# Modelo físico simplificado: Q ∝ k*h*φ*p + ruído
producao_teorica = 0.1 * k * h * phi * p / 1000
ruido = np.random.normal(0, 0.2, n_pocos)
producao = np.clip(producao_teorica + ruido, 0.5, None)

dados = pd.DataFrame({
    'Porosidade': phi,
    'Permeabilidade': k,
    'Espessura': h,
    'Pressao': p,
    'Producao': producao
})

print("=== DADOS DO RESERVATÓRIO ===")
print(dados.head())

X_features = dados[['Porosidade', 'Permeabilidade', 'Espessura', 'Pressao']].values
y_target = dados['Producao'].values

# ============================================================================
# SUA TAREFA: IMPLEMENTAR O MMQ MATRICIAL OU VIA SKTLEARN
# ============================================================================
# 1. Crie a matriz auxiliar (adicionando a coluna de 1s ao X_features)
# 2. Calcule o vetor beta usando a álgebra linear: beta = (X'X)^-1 * X'y

# >>> SEU CÓDIGO AQUI <<<
# >>> VISUALIZAÇÕES <<<

# DICA: Substitua o array de zeros abaixo pelo seu vetor 'beta' calculado
beta = np.zeros(5)

# ============================================================================
# RESULTADO ESPERADO
# ============================================================================
print(f"\n=== EQUAÇÃO FINAL DO MODELO ===")
print(f"Produção = {beta[0]:.3f} + {beta[1]:.3f}×Porosidade + {beta[2]:.6f}×Permeabilidade + {beta[3]:.3f}×Espessura + {beta[4]:.3f}×Pressao")