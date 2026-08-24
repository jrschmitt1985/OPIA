import numpy as np
import pandas as pd

np.random.seed(123)
n_pocos = 50

phi = np.random.uniform(0.08, 0.25, n_pocos)      # Porosidade (8% a 25%)
k = np.random.lognormal(3, 1, n_pocos)            # Permeabilidade (distribuição log-normal)
k = np.clip(k, 10, 1000)                          # Limita a permeabilidade entre 10 e 1000 mD
h = np.random.uniform(10, 50, n_pocos)            # Espessura útil do reservatório (10 a 50 metros)
p = np.random.uniform(200, 400, n_pocos)          # Pressão inicial (200 a 400 psi)

producao_teorica = 0.1 * k * h * phi * p / 1000
ruido = np.random.normal(0, 0.2, n_pocos)
producao = np.clip(producao_teorica + ruido, 0.5, None)  # Garante produção física mínima de 0.5 bbl/dia

dados = pd.DataFrame({
    'Porosidade': phi,
    'Permeabilidade': k,
    'Espessura': h,
    'Pressao': p,
    'Producao': producao
})

print("=== DADOS DO RESERVATÓRIO (Primeiras Linhas) ===")
print(dados.head())

y = dados['Producao'].values
X_raw = dados[['Porosidade', 'Permeabilidade', 'Espessura', 'Pressao']].values
uns = np.ones((n_pocos, 1))
X = np.hstack((uns, X_raw))

print("=== DIMENSÕES DAS MATRIZES ===")
print(f"Formato de X: {X.shape}")  # Deve mostrar (50, 5)
print(f"Formato de y: {y.shape}")  # Deve mostrar (50,)

print("\n=== PRIMEIRA LINHA DE X (com o 1 do intercepto) ===")
print(X[0])