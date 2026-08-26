import numpy as np
import pandas as pd
## geracao de poços artificiais
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

X_transposta = X.T
X_transposta_X = X_transposta @ X
inversa_X_transposta_X = np.linalg.inv(X_transposta_X)

beta = inversa_X_transposta_X @ X_transposta @ y
nomes_variaveis = ['Intercepto (beta_0)', 'Porosidade (beta_1)', 'Permeabilidade (beta_2)', 'Espessura (beta_3)', 'Pressao (beta_4)']
print("=== COEFICIENTES ESTIMADOS PELO MMQ ===")
for nome, valor in zip(nomes_variaveis, beta):
    print(f"{nome}: {valor:.6f}")


y_pred = X @ beta  # Multiplicação matricial (50,5) @ (5,) -> (50,)
y_media = np.mean(y)
sst = np.sum((y - y_media) ** 2)
ssr = np.sum((y - y_pred) ** 2)
r2_manual = 1 - (ssr / sst)

mse_manual = np.mean((y - y_pred) ** 2)  # Média dos erros ao quadrado
rmse_manual = np.sqrt(mse_manual)         # Raiz quadrada

print("\n=== METRICAS DE RENDIMENTO ESTADISTICO ===")
print(f"R² do modelo (manual): {r2_manual:.4f}")
print(f"RMSE do modelo (manual): {rmse_manual:.4f} bbl/dia")

## com o codigo pronto agora podemos criar variacoes:

# 1. Definir as propriedades do novo poço prospectivo (phi, k, h, p)
novo_poco = np.array([0.18, 150.0, 25.0, 300.0])

novo_poco_com_intercepto = np.concatenate([[1.0], novo_poco])
producao_prevista = novo_poco_com_intercepto @ beta

print("\n=== RESULTADO DA PREDIÇÃO ===")
print(f"Poço Novo -> φ=18%, k=150 mD, h=25 m, p=300 psi")
print(f"Produção estimada: {producao_prevista:.4f} bbl/dia")