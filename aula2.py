import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')


plt.style.use('seaborn-v0_8')
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 12

print("Bibliotecas importadas com sucesso!")
print("Configurações de visualização aplicadas!")

# =============================================================================
# CÉLULA 3: EXERCÍCIO 1 - DADOS DOS POÇOS
# =============================================================================

print("\n" + "="*60)
print("🔢 EXERCÍCIO 1: OPERAÇÕES COM VETORES")
print("="*60)

# Propriedades petrofísicas de 3 poços
# Formato: [Porosidade, Permeabilidade(mD), Saturação_água]
poco1 = np.array([0.15, 100, 0.30])  # Poço 1
poco2 = np.array([0.18, 120, 0.25])  # Poço 2
poco3 = np.array([0.12, 80, 0.35])   # Poço 3

print("DADOS DOS POÇOS:")
print(f"Poço 1: φ={poco1[0]:.2f}, k={poco1[1]:.0f}mD, Sw={poco1[2]:.2f}")
print(f"Poço 2: φ={poco2[0]:.2f}, k={poco2[1]:.0f}mD, Sw={poco2[2]:.2f}")
print(f"Poço 3: φ={poco3[0]:.2f}, k={poco3[1]:.0f}mD, Sw={poco3[2]:.2f}")


# =============================================================================
# CÉLULA 4: EXERCÍCIO 1 - CÁLCULOS COM VETORES
# =============================================================================

print("\n📈 CÁLCULOS:")

# 1. Propriedades médias
media = (poco1 + poco2 + poco3) / 3
print(f"Propriedades médias: φ={media[0]:.3f}, k={media[1]:.1f}mD, Sw={media[2]:.3f}")

# 2. Distâncias euclidianas
dist_1_2 = np.linalg.norm(poco1 - poco2) #distância linear entre dois pontos
dist_1_3 = np.linalg.norm(poco1 - poco3)
dist_2_3 = np.linalg.norm(poco2 - poco3)

print(f"\nDISTÂNCIAS EUCLIDIANAS:")
print(f"Distância Poço 1-2: {dist_1_2:.2f}")
print(f"Distância Poço 1-3: {dist_1_3:.2f}")
print(f"Distância Poço 2-3: {dist_2_3:.2f}")

# 3. Produto escalar (similaridade)
sim_1_2 = np.dot(poco1, poco2)
sim_1_3 = np.dot(poco1, poco3)
sim_2_3 = np.dot(poco2, poco3)

print(f"\nPRODUTOS ESCALARES (Similaridade):")
print(f"Similaridade Poço 1-2: {sim_1_2:.1f}")
print(f"Similaridade Poço 1-3: {sim_1_3:.1f}")
print(f"Similaridade Poço 2-3: {sim_2_3:.1f}")

# =============================================================================
# CÉLULA 5: EXERCÍCIO 1 - INTERPRETAÇÃO GEOLÓGICA
# =============================================================================

print(f"\n INTERPRETAÇÃO GEOLÓGICA:")
pocos_similares = min([(dist_1_2, "1-2"), (dist_1_3, "1-3"), (dist_2_3, "2-3")])
print(f"Poços mais similares: {pocos_similares[1]} (distância: {pocos_similares[0]:.2f})")

if media[0] > 0.15:
    print("✅ Reservatório com boa porosidade média (>15%)")
else:
    print("⚠️ Reservatório com porosidade moderada (<15%)")


# =============================================================================
# CÉLULA 6: EXERCÍCIO 2 - CRIAR MATRIZ DE DADOS
# =============================================================================

print("\n" + "="*60)
print("EXERCÍCIO 2: MATRIZES E DATAFRAMES")
print("="*60)

# Criar matriz de dados de múltiplos poços
dados_matriz = np.array([
    [0.15, 100, 0.30, 2500],  # Poço 1
    [0.18, 120, 0.25, 2480],  # Poço 2
    [0.12, 80, 0.35, 2520],   # Poço 3
    [0.20, 150, 0.25, 2460],  # Poço 4
    [0.14, 90, 0.40, 2540],   # Poço 5
    [0.22, 180, 0.20, 2420]   # Poço 6
])

# Criar DataFrame estruturado
df = pd.DataFrame(dados_matriz,
                  columns=['Porosidade', 'Permeabilidade', 'Sat_Agua', 'Profundidade'],
                  index=[f'Poço_{i+1}' for i in range(len(dados_matriz))])

print("📋 DATAFRAME DOS POÇOS:")
print(df)


# =============================================================================
# CÉLULA 7: EXERCÍCIO 2 - ESTATÍSTICAS E CORRELAÇÃO
# =============================================================================

print(f"\n📊 ESTATÍSTICAS DESCRITIVAS:")
print(df.describe())

# Matriz de correlação
print(f"\n🔗 MATRIZ DE CORRELAÇÃO:")
correlacao = df.corr()
print(correlacao.round(3))

# =============================================================================
# CÉLULA 8: EXERCÍCIO 2 - VISUALIZAÇÃO DA CORRELAÇÃO
# =============================================================================

# Visualização da matriz de correlação
plt.figure(figsize=(10, 8),dpi=200)
sns.heatmap(correlacao,
            annot=True,
            cmap='coolwarm',
            center=0,
            square=True,
            fmt='.3f')
plt.title('Matriz de Correlação - Propriedades Petrofísicas')
plt.tight_layout()
plt.show()

# =============================================================================
# CÉLULA 9: EXERCÍCIO 2 - INTERPRETAÇÃO DAS CORRELAÇÕES
# =============================================================================

print(f"\nINTERPRETAÇÃO DAS CORRELAÇÕES:")
corr_phi_k = correlacao.loc['Porosidade', 'Permeabilidade']
corr_phi_sw = correlacao.loc['Porosidade', 'Sat_Agua']

print(f"Porosidade vs Permeabilidade: r = {corr_phi_k:.3f}")
if corr_phi_k > 0.5:
    print("  ✅ Forte correlação positiva (esperado geologicamente)")
elif corr_phi_k > 0:
    print("  ⚠️ Correlação positiva moderada")
else:
    print("  ❌ Correlação negativa (revisar dados)")

print(f"\nPorosidade vs Saturação de Água: r = {corr_phi_sw:.3f}")
if corr_phi_sw < -0.3:
    print("  ✅ Correlação negativa (maior φ, menor Sw - bom sinal)")
elif corr_phi_sw < 0:
    print("  ⚠️ Correlação negativa fraca")
else:
    print("  ❌ Correlação positiva (revisar - pode indicar problema)")