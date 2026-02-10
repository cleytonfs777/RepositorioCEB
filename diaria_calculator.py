#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
calc_diarias_cbmmg.py
Reprodução 1:1 da lógica da planilha "Cálculo de Diária - 75 reais.xlsx"

O script:
- Classifica o destino: Capital / Município Especial / Demais Municípios (e "outro estado" -> Especial)
- Calcula DI e PA conforme a aba "CALCULO N DIÁRIAS"
- Distribui para L (Diárias), M (PA), N (PP) conforme a planilha
- Calcula o valor unitário K:
    K = max(piso_localidade, round(H * valor_dia_posto, 2))
- Calcula o total:
    total = round((K/2 - ajuda) * M, 2) + round((K - ajuda) * L, 2) + round((K/2) * N, 2)

⚠️ Importante:
- Você precisa informar/fornecer a tabela de "valor-dia" por graduação (o que a planilha pega por VLOOKUP na aba DADOS).
  Você pode preencher o dicionário VALOR_DIA_POR_GRADUACAO com seus valores reais.
- Municípios especiais são lidos do DOCX "Relação dos Municípios Especiais" (python-docx).
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Set, Tuple

from docx import Document


# ----------------------------
# Pisos por localidade (iguais aos da sua planilha)
# ----------------------------
PISOS_LOCALIDADE = {
    "Capital": 470.00,
    "Município Especial": 362.00,
    "Demais Municípios": 258.00,
}

# ----------------------------
# Capitais (normalizadas)
# ----------------------------
CAPITAIS_BR = {
    "aracaju", "belem", "belo horizonte", "boa vista", "brasilia", "campo grande",
    "cuiaba", "curitiba", "florianopolis", "fortaleza", "goiania", "joao pessoa",
    "macapa", "maceio", "manaus", "natal", "palmas", "porto alegre", "porto velho",
    "recife", "rio branco", "rio de janeiro", "salvador", "sao luis", "sao paulo",
    "teresina", "vitoria",
}

# ----------------------------
# TABELA: valor-dia por graduação/posto (você deve preencher!)
# Na planilha isso vem de: VLOOKUP(GRAD, DADOS!D2:F22, 3)
# ----------------------------
VALOR_DIA_POR_GRADUACAO: Dict[str, float] = {
    # EXEMPLO (substitua pelos seus valores reais):
    # "CAP": 15276.62 / 30,
    # "TEN": 12000.00 / 30,
}


# ----------------------------
# Utilidades
# ----------------------------
def norm(s: str) -> str:
    return " ".join(s.strip().lower().split())


def parse_dt(s: str) -> datetime:
    """Formato esperado: YYYY-MM-DD HH:MM"""
    return datetime.strptime(s, "%Y-%m-%d %H:%M")


def carregar_municipios_especiais(docx_path: Path) -> Set[str]:
    """Lê o DOCX anexado pelo usuário e retorna set normalizado."""
    doc = Document(str(docx_path))
    especiais: Set[str] = set()
    for p in doc.paragraphs:
        t = p.text.strip()
        if not t:
            continue
        if t.replace(".", "").isdigit():  # ignora 1., 2., etc
            continue
        especiais.add(norm(t))
    return especiais


def classificar_destino(municipio: str, outro_estado: bool, especiais_mg: Set[str]) -> str:
    """
    Replica a lógica da planilha:

    - Se NÃO está em especiais e NÃO está em capitais e outro_estado == False => Demais Municípios
    - Se NÃO está em especiais e NÃO está em capitais e outro_estado == True  => Município Especial
    - Se está em capitais => Capital
    - Senão => Município Especial
    """
    m = norm(municipio)
    in_especiais = m in especiais_mg
    in_capitais = m in CAPITAIS_BR

    if (not in_especiais) and (not in_capitais) and (not outro_estado):
        return "Demais Municípios"
    if (not in_especiais) and (not in_capitais) and outro_estado:
        return "Município Especial"
    if in_capitais:
        return "Capital"
    return "Município Especial"


# ----------------------------
# Cálculo DI/PA - réplica da aba "CALCULO N DIÁRIAS"
# ----------------------------
def calcular_di_pa_planilha(inicio: datetime, fim: datetime) -> Tuple[int, int]:
    """
    Replica:
      B7 = INT(fim - inicio)                     -> dias completos (DI base)
      C7 = ROUND(MOD(fim-inicio,1)*24,2)         -> horas do resto
      Ajuste: se hora_fim < hora_inicio => DI = B7 + 1
      PA: se hora_fim >= hora_inicio e resto_horas >= 6 => 1, senão 0
    """
    if fim <= inicio:
        raise ValueError("fim deve ser maior que inicio")

    delta = fim - inicio
    dias_inteiros = int(delta.total_seconds() // (24 * 3600))

    resto = delta - timedelta(days=dias_inteiros)
    resto_horas = round(resto.total_seconds() / 3600.0, 2)

    hora_inicio = inicio.time()
    hora_fim = fim.time()

    di = dias_inteiros + (1 if hora_fim < hora_inicio else 0)
    pa = 1 if (hora_fim >= hora_inicio and resto_horas >= 6.0) else 0
    return di, pa


def distribuir_quantidades(di: int, pa: int, tem_pousada: bool) -> Tuple[int, int, int]:
    """
    Mapeia para L (Diárias), M (PA), N (PP) conforme a planilha:

    - Se tem pousada:
        L = DI
        M = PA (0 ou 1)
        N = DI   (PP acompanha cada DI)
    - Se não tem pousada:
        L = 0
        N = 0
        M = DI + PA  (tudo vira PA)
    """
    if tem_pousada:
        return di, pa, di
    return 0, di + pa, 0


# ----------------------------
# Fator H - réplica da planilha
# ----------------------------
def calc_g(quinquenios: int, ade: float | None) -> float:
    # G = IF(ISBLANK(ADE), quinquenios, ADE/10)
    if ade is None:
        return float(quinquenios)
    return float(ade) / 10.0


def calc_h(tipo_trintenario: str, g: float) -> float:
    """
    H =
      se "Sim - anterior a 1ºSet07": (1 + g/10) * 1.1
      se "Sim - Posterior a 1ºSet07": 1.1 + g/10
      senão: 1 + g/10
    """
    tipo = tipo_trintenario.strip()
    if tipo == "Sim - anterior a 1ºSet07":
        return (1.0 + g / 10.0) * 1.1
    if tipo == "Sim - Posterior a 1ºSet07":
        return 1.1 + g / 10.0
    return 1.0 + g / 10.0


# ----------------------------
# Valor unitário K e Total - réplica da planilha
# ----------------------------
def calcular_k(graduacao: str, localidade: str, h: float, valor_dia_por_grad: Dict[str, float]) -> float:
    grad = graduacao.strip().upper()
    if grad not in valor_dia_por_grad:
        raise KeyError(
            f"Graduação '{grad}' não encontrada na tabela VALOR_DIA_POR_GRADUACAO. "
            f"Preencha o dicionário no código com os valores reais (valor-dia)."
        )
    valor_dia = float(valor_dia_por_grad[grad])
    j = round(h * valor_dia, 2)
    piso = float(PISOS_LOCALIDADE[localidade])
    return round(max(piso, j), 2)


def calcular_total(k: float, l_diarias: int, m_pas: int, n_pp: int, ajuda_custo: float) -> float:
    """
    total = round((k/2 - ajuda) * M, 2) + round((k - ajuda) * L, 2) + round((k/2) * N, 2)
    """
    k = round(k, 2)
    parte_pa = round((k / 2.0 - ajuda_custo), 2) * m_pas
    parte_di = round((k - ajuda_custo), 2) * l_diarias
    parte_pp = round((k / 2.0), 2) * n_pp
    return round(parte_pa + parte_di + parte_pp, 2)


@dataclass
class Resultado:
    localidade: str
    di: int
    pa: int
    L_diarias: int
    M_pas: int
    N_pp: int
    g: float
    h: float
    k: float
    total: float


def main() -> None:
    ap = argparse.ArgumentParser(description="Cálculo de diárias (réplica da planilha) - CBMMG")
    ap.add_argument("--graduacao", required=True, help="Ex: CAP, TEN, SGT, CB...")
    ap.add_argument("--quinquenios", type=int, default=0, help="Qtd quinquênios (usado se ADE não informado)")
    ap.add_argument("--ade", type=float, default=None, help="ADE numérico (se informado, substitui quinquênios; vira ADE/10)")
    ap.add_argument(
        "--trintenario",
        default="Não",
        choices=["Não", "Sim - anterior a 1ºSet07", "Sim - Posterior a 1ºSet07"],
        help="Tipo de adicional trintenário",
    )
    ap.add_argument("--municipio", required=True, help="Município de destino")
    ap.add_argument("--outro-estado", action="store_true", help="Marque se o destino é fora de MG")
    ap.add_argument("--inicio", required=True, help='YYYY-MM-DD HH:MM')
    ap.add_argument("--fim", required=True, help='YYYY-MM-DD HH:MM')
    ap.add_argument("--pousada", action="store_true", help="Marque se há pousada/pernoite (B5='Sim')")
    ap.add_argument("--ajuda-custo", type=float, default=74.98, help="Ajuda de custo (planilha ~74,98)")
    ap.add_argument("--docx-municipios-especiais", required=True, help="Caminho do DOCX de municípios especiais")

    args = ap.parse_args()

    especiais = carregar_municipios_especiais(Path(args.docx_municipios_especiais))
    localidade = classificar_destino(args.municipio, bool(args.outro_estado), especiais)

    inicio = parse_dt(args.inicio)
    fim = parse_dt(args.fim)

    di, pa = calcular_di_pa_planilha(inicio, fim)
    L, M, N = distribuir_quantidades(di, pa, bool(args.pousada))

    g = calc_g(args.quinquenios, args.ade)
    h = calc_h(args.trintenario, g)

    k = calcular_k(args.graduacao, localidade, h, VALOR_DIA_POR_GRADUACAO)
    total = calcular_total(k, L, M, N, float(args.ajuda_custo))

    res = Resultado(
        localidade=localidade, di=di, pa=pa,
        L_diarias=L, M_pas=M, N_pp=N,
        g=g, h=h, k=k, total=total
    )

    print("\n=== RESULTADO (réplica da planilha) ===")
    print(f"Destino: {args.municipio} | Outro estado: {bool(args.outro_estado)}")
    print(f"Localidade classificada: {res.localidade}")
    print(f"DI (planilha): {res.di}")
    print(f"PA (planilha): {res.pa}")
    print(f"L (Diárias): {res.L_diarias}")
    print(f"M (PAs): {res.M_pas}")
    print(f"N (PP): {res.N_pp}")
    print(f"Fator G: {res.g:.4f}")
    print(f"Fator H: {res.h:.4f}")
    print(f"K (valor unitário DI integral): R$ {res.k:.2f}")
    print(f"TOTAL: R$ {res.total:.2f}\n")


if __name__ == "__main__":
    main()
