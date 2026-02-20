from diaria_calculator import calcular_diarias

res = calcular_diarias(
    graduacao="Cap",
    municipio="Betim",
    inicio="2025-12-19 07:00",
    fim="2025-12-22 18:00",
    quinquenios=2,
    trintenario="Não",
    outro_estado=False,
    pousada=False,
    ajuda_custo=74.98,
)

print(res)           # dataclass completo
print(res.total)     # total calculado
print(res.k)         # valor unitário K
print(res.localidade)