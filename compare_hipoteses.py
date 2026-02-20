"""
Testando diferentes cenários para identificar a lógica correta de DI/PA
"""
from datetime import datetime

def calcular_h1(inicio, fim):
    """H1: resto >= 12h => PA (nunca vira DI adicional por tempo)"""
    delta = fim - inicio
    dias_inteiros = int(delta.total_seconds() // (24 * 3600))
    resto_horas = (delta.total_seconds() % (24 * 3600)) / 3600
    
    di = dias_inteiros
    pa = 1 if resto_horas >= 12.0 else (1 if resto_horas >= 6.0 else 0)
    return di, pa

def calcular_h2(inicio, fim):
    """H2: hora_fim >= hora_inicio + resto >= 6h => PA (não importa se >= 12h)"""
    delta = fim - inicio
    dias_inteiros = int(delta.total_seconds() // (24 * 3600))
    resto_horas = (delta.total_seconds() % (24 * 3600)) / 3600
    hora_inicio = inicio.time()
    hora_fim = fim.time()
    
    di = dias_inteiros
    pa = 0
    if hora_fim >= hora_inicio:
        if resto_horas >= 6.0:
            pa = 1
    else:
        di += 1
    return di, pa

def calcular_h3(inicio, fim):
    """H3: 6h <= resto < 18h => PA; resto >= 18h => +DI"""
    delta = fim - inicio
    dias_inteiros = int(delta.total_seconds() // (24 * 3600))
    resto_horas = (delta.total_seconds() % (24 * 3600)) / 3600
    hora_inicio = inicio.time()
    hora_fim = fim.time()
    
    di = dias_inteiros
    pa = 0
    if hora_fim >= hora_inicio:
        if resto_horas >= 18.0:
            di += 1
        elif resto_horas >= 6.0:
            pa = 1
    else:
        di += 1
    return di, pa

# Cenários de teste
cenarios = [
    ("01-12-2025 06:00", "05-12-2025 18:00", "4 dias + 12h"),  # caso original
    ("01-12-2025 06:00", "05-12-2025 12:00", "4 dias + 6h"),   # exatamente 6h
    ("01-12-2025 06:00", "05-12-2025 09:00", "4 dias + 3h"),   # menos de 6h
    ("01-12-2025 06:00", "06-12-2025 00:00", "4 dias + 18h"),  # exatamente 18h
    ("01-12-2025 06:00", "06-12-2025 06:00", "5 dias + 0h"),   # exato
    ("01-12-2025 06:00", "05-12-2025 03:00", "volta no tempo do dia"),  # hora_fim < hora_inicio
    ("01-12-2025 14:00", "05-12-2025 20:00", "4 dias + 6h (tarde)"),
]

print("=" * 90)
print("COMPARAÇÃO DE HIPÓTESES")
print("=" * 90)
print(f"{'Cenário':<35} | {'H1':<8} | {'H2':<8} | {'H3':<8}")
print("-" * 90)

for inicio_str, fim_str, desc in cenarios:
    try:
        inicio = datetime.strptime(inicio_str, "%d-%m-%Y %H:%M")
        fim = datetime.strptime(fim_str, "%d-%m-%Y %H:%M")
        
        di_h1, pa_h1 = calcular_h1(inicio, fim)
        di_h2, pa_h2 = calcular_h2(inicio, fim)
        di_h3, pa_h3 = calcular_h3(inicio, fim)
        
        print(f"{desc:<35} | {di_h1}DI+{pa_h1}PA | {di_h2}DI+{pa_h2}PA | {di_h3}DI+{pa_h3}PA")
    except:
        print(f"{desc:<35} | ERRO")

print()
print("=" * 90)
print("DESCRIÇÃO DAS HIPÓTESES")
print("=" * 90)
print("H1: Se resto >= 12h => PA (não vira DI adicional)")
print("    Se 6h <= resto < 12h => PA")
print("    Se resto < 6h => nada")
print()
print("H2: Se hora_fim >= hora_início E resto >= 6h => PA (qualquer resto >= 6h vira PA)")
print("    Se hora_fim < hora_início => +1 DI (virou dia seguinte)")
print()
print("H3: Se 6h <= resto < 18h => PA")
print("    Se resto >= 18h => +1 DI")
print("    Se hora_fim < hora_início => +1 DI")
print()
print("=" * 90)
print("DIFERENÇAS PRINCIPAIS:")
print("- H1 e H2 divergem no cenário de 18h+ (H1=PA, H2=PA, H3=DI)")
print("- H2 e H3 divergem quando hora_fim >= hora_início (H2 sempre PA se >=6h)")
