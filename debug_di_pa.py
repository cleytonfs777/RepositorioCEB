from datetime import datetime, timedelta

inicio = datetime.strptime("2025-12-01 06:00", "%Y-%m-%d %H:%M")
fim = datetime.strptime("2025-12-05 18:00", "%Y-%m-%d %H:%M")

print("=== ANÁLISE DO CÁLCULO DI/PA ===")
print(f"Início: {inicio}")
print(f"Fim: {fim}")
print()

delta = fim - inicio
print(f"Delta total: {delta}")
print(f"Delta em dias: {delta.total_seconds() / (24*3600):.4f} dias")
print(f"Delta em horas: {delta.total_seconds() / 3600:.2f} horas")
print()

dias_inteiros = int(delta.total_seconds() // (24 * 3600))
resto = delta - timedelta(days=dias_inteiros)
resto_horas = round(resto.total_seconds() / 3600.0, 2)

print(f"Dias inteiros: {dias_inteiros}")
print(f"Resto: {resto}")
print(f"Resto em horas: {resto_horas}")
print()

hora_inicio = inicio.time()
hora_fim = fim.time()

print(f"Hora início: {hora_inicio}")
print(f"Hora fim: {hora_fim}")
print(f"Hora fim >= Hora início? {hora_fim >= hora_inicio}")
print()

# Lógica atual do script
di_atual = dias_inteiros + (1 if hora_fim < hora_inicio else 0)
pa_atual = 0
if hora_fim >= hora_inicio:
    if resto_horas >= 12.0:
        di_atual += 1
    elif resto_horas >= 6.0:
        pa_atual = 1

print("=== LÓGICA ATUAL DO SCRIPT ===")
print(f"DI = {di_atual}")
print(f"PA = {pa_atual}")
print()

# Valores esperados da planilha
print("=== VALORES DA PLANILHA ===")
print(f"DI = 4")
print(f"PA = 1")
print()

# Análise: se a planilha dá 4 DI + 1 PA, então:
# As 12 horas do resto não estão sendo contadas como +1 DI, mas como 1 PA
print("=== ANÁLISE ===")
print("A diferença é que quando resto_horas >= 12 E hora_fim >= hora_inicio:")
print("  - Script atual: adiciona +1 DI")
print("  - Planilha: considera como 1 PA?")
print()

# Testando lógica alternativa
print("=== TESTANDO LÓGICAS ALTERNATIVAS ===")
print()

# Hipótese 1: resto >= 12h sempre vira PA, não DI adicional
print("H1: Se resto >= 12h => 1 PA (não adiciona DI)")
di_h1 = dias_inteiros
pa_h1 = 1 if resto_horas >= 12.0 else (1 if resto_horas >= 6.0 else 0)
print(f"  DI = {di_h1}, PA = {pa_h1}")
print(f"  MATCH! ✓" if (di_h1 == 4 and pa_h1 == 1) else "  Não match")
print()

# Hipótese 2: a condição hora_fim >= hora_inicio muda tudo
print("H2: Se hora_fim >= hora_inicio AND resto >= 6h => 1 PA")
print("    (não adiciona DI independente de ser >= 12h)")
di_h2 = dias_inteiros
pa_h2 = 0
if hora_fim >= hora_inicio:
    if resto_horas >= 6.0:
        pa_h2 = 1
else:
    di_h2 += 1
print(f"  DI = {di_h2}, PA = {pa_h2}")
print(f"  MATCH! ✓" if (di_h2 == 4 and pa_h2 == 1) else "  Não match")
print()

# Hipótese 3: diferentes limiares para PA vs DI
print("H3: 6h <= resto < 18h => PA; resto >= 18h => +DI")
di_h3 = dias_inteiros
pa_h3 = 0
if hora_fim >= hora_inicio:
    if resto_horas >= 18.0:
        di_h3 += 1
    elif resto_horas >= 6.0:
        pa_h3 = 1
else:
    di_h3 += 1
print(f"  DI = {di_h3}, PA = {pa_h3}")
print(f"  MATCH! ✓" if (di_h3 == 4 and pa_h3 == 1) else "  Não match")
