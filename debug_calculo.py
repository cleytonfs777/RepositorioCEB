from diaria_calculator import calcular_diarias

# Dados do teste
res = calcular_diarias(
    graduacao="Cap",
    municipio="Betim",
    inicio="2026-12-01 06:00",
    fim="2026-12-05 18:00",
    quinquenios=3,
    trintenario="Não",
    outro_estado=False,
    pousada=False,
    ajuda_custo=74.98,
)

print("=== ANÁLISE DO CÁLCULO ===")
print(f"K (unitária) = {res.k}")
print(f"L (Diárias inteiras) = {res.L_diarias}")
print(f"M (PAs) = {res.M_pas}")
print(f"N (PP) = {res.N_pp}")
print(f"Ajuda de custo = 74.98")
print()

# Cálculo atual do script
ajuda = 74.98
parte_pa = round((res.k / 2.0 - ajuda), 2) * res.M_pas
parte_di = round((res.k - ajuda), 2) * res.L_diarias
parte_pp = round((res.k / 2.0), 2) * res.N_pp

print("=== FÓRMULA ATUAL (script) ===")
print(f"Parte PA: round((K/2 - ajuda), 2) * M = round(({res.k}/2 - {ajuda}), 2) * {res.M_pas}")
print(f"        = round({res.k/2 - ajuda}, 2) * {res.M_pas} = {round(res.k/2 - ajuda, 2)} * {res.M_pas} = {parte_pa}")
print()
print(f"Parte DI: round((K - ajuda), 2) * L = round(({res.k} - {ajuda}), 2) * {res.L_diarias}")
print(f"        = {round(res.k - ajuda, 2)} * {res.L_diarias} = {parte_di}")
print()
print(f"Parte PP: round(K/2, 2) * N = {round(res.k/2, 2)} * {res.N_pp} = {parte_pp}")
print()
print(f"TOTAL (script) = {parte_pa} + {parte_di} + {parte_pp} = {res.total}")
print()

# Valor esperado da planilha
total_planilha = 2604.06
print(f"TOTAL (planilha) = {total_planilha}")
print(f"DIFERENÇA = {res.total} - {total_planilha} = {res.total - total_planilha}")
print()

# Análise da diferença
print("=== ANÁLISE DA DIFERENÇA ===")
print(f"Diferença = {res.total - total_planilha:.2f}")
print(f"K/2 = {res.k/2:.2f}")
print(f"Diferença / K = {(res.total - total_planilha) / res.k:.4f}")
print()

# Tentando descobrir a fórmula correta
print("=== TESTANDO FÓRMULAS ALTERNATIVAS ===")
print()

# Hipótese 1: Ajuda não é descontada de cada diária, mas apenas uma vez do total
total_h1 = (res.k * res.L_diarias) - ajuda
print(f"H1: (K * L) - ajuda = ({res.k} * {res.L_diarias}) - {ajuda} = {total_h1:.2f}")
print(f"    Diferença com planilha: {abs(total_h1 - total_planilha):.2f}")
print()

# Hipótese 2: Diárias inteiras usam K/2 + algo
valor_unitario_necessario = total_planilha / res.L_diarias
print(f"H2: Valor unitário necessário = {total_planilha} / {res.L_diarias} = {valor_unitario_necessario:.2f}")
print(f"    K - valor_necessário = {res.k} - {valor_unitario_necessario:.2f} = {res.k - valor_unitario_necessario:.2f}")
print(f"    (desconto aplicado por diária)")
print()

# Hipótese 3: Ajuda é aplicada de forma diferente para diárias inteiras
# Talvez seja (K/2 + K/2 - ajuda) ou algo assim
print("H3: Testando se diárias inteiras = K/2 + (K/2 - ajuda)")
total_h3 = (res.k/2 + (res.k/2 - ajuda)) * res.L_diarias
print(f"    Total = (K/2 + (K/2 - ajuda)) * L = ({res.k/2:.2f} + {res.k/2 - ajuda:.2f}) * {res.L_diarias}")
print(f"    Total = {total_h3:.2f}")
print(f"    Diferença com planilha: {abs(total_h3 - total_planilha):.2f}")
print()

# Hipótese 4: Ajuda é aplicada sobre K (não K - ajuda para cada diária)
# Ou seja, a ajuda é dividida proporcionalmente
print("H4: Testando se ajuda é aplicada por período, não por diária")
total_h4 = res.k * res.L_diarias - ajuda * res.L_diarias
print(f"    Total = K * L - ajuda * L = {res.k} * {res.L_diarias} - {ajuda} * {res.L_diarias}")
print(f"    Total = {total_h4:.2f}")
print(f"    (mesma coisa que a fórmula atual!)")
