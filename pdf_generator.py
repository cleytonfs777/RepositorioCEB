from __future__ import annotations

import re
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List, Any, Tuple

from pypdf import PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Preformatted,  # mantém colunas fixas (não bagunça 3270)
)


# ============================================================
# 1) Máscara + limpeza (SEM destruir espaçamento do terminal)
# ============================================================
def mask_sensitive(text: str) -> str:
    # CPF 000.000.000-00 -> ***.***.***-**
    text = re.sub(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b", "***.***.***-**", text)

    # PIS/PASEP (ex.: 1292809110-8) -> **********-*
    text = re.sub(r"\b\d{10}-\d\b", "**********-*", text)

    # RG tipo MG-19674285 -> MG-******85 (mantém final)
    def rg_mask(m: re.Match) -> str:
        uf = m.group(1)
        num = m.group(2)
        return f"{uf}-******{num[-2:]}" if len(num) >= 2 else f"{uf}-******"

    text = re.sub(r"\b([A-Z]{1,3})-?(\d{4,10})\b", rg_mask, text)

    # Conta (conservador): CONTA :12725 -> CONTA :****
    text = re.sub(r"(CONTA\s*:)\s*\d+", r"\1 ****", text, flags=re.IGNORECASE)

    return text


def normalize_screen_text(screen: str) -> str:
    """
    Normaliza EOL e reduz excesso de linhas vazias, sem mexer em espaços internos.
    """
    screen = (screen or "").replace("\r\n", "\n").replace("\r", "\n")
    screen = re.sub(r"\n{3,}", "\n\n", screen)
    return mask_sensitive(screen).rstrip("\n")


# ============================================================
# 2) Correção de "wrap" do 3270 (C + LEYTON, C + HEFE, etc.)
# ============================================================
def _repair_wrapped_word_lines(lines: List[str], max_cols: int) -> List[str]:
    """
    Corrige quebras típicas do terminal (wrap no limite de coluna):
      "... -C" + "\n" + "LEYTON ..."  -> "... -CLEYTON ..." e "LEYTON" vira espaços na linha de baixo
      "...  C" + "\n" + "HEFE ..."    -> "...  CHEFE ..."   e "HEFE" vira espaços na linha de baixo

    Importante: NÃO desloca a linha de baixo para a esquerda (preserva colunas).
    """
    out = lines[:]  # cópia

    for i in range(len(out) - 1):
        a = out[i]
        b = out[i + 1]

        if not a or not b:
            continue

        a_rstrip = a.rstrip()
        if not a_rstrip:
            continue

        # Só mexe se a linha A estiver "cheia" (perto do limite)
        # wrap costuma ocorrer no final da linha
        end_idx = len(a_rstrip)
        if end_idx < max_cols - 6:
            continue

        # token inicial da linha B (primeira palavra)
        m_b = re.match(r"([A-Z0-9/.\-]{2,})(.*)$", b)
        if not m_b:
            continue

        token = m_b.group(1)
        rest = m_b.group(2)

        # Caso 1: termina com "-X" (ex: "-C")
        dash_tail = re.search(r"(-[A-Z])$", a_rstrip)

        # Caso 2: termina com letra solta " X" (ex: "... C")
        one_tail = re.search(r"([A-Z])$", a_rstrip)
        one_tail_ok = bool(one_tail and len(a_rstrip) >= 2 and a_rstrip[-2] == " ")

        if not dash_tail and not one_tail_ok:
            continue

        # Aplica fix: concatena token na linha A
        a_fixed = a_rstrip + token

        # E substitui o token no início da linha B por espaços do mesmo tamanho
        b_fixed = (" " * len(token)) + rest

        out[i] = a_fixed
        out[i + 1] = b_fixed

    return out


def format_terminal_text(text: str, max_cols: int = 92) -> str:
    """
    Formata texto 3270 preservando layout:
    - corrige wrap de tokens sem deslocar colunas
    - padroniza largura de cada linha (corta / completa)
    """
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")

    # 1) corrige tokens quebrados pelo wrap
    lines = _repair_wrapped_word_lines(lines, max_cols=max_cols)

    # 2) padroniza largura e mantém espaços
    out_lines: List[str] = []
    for line in lines:
        line = line.replace("\t", "    ").rstrip("\n\r")

        if len(line) > max_cols:
            line = line[:max_cols]
        else:
            line = line.ljust(max_cols)

        out_lines.append(line)

    return "\n".join(out_lines)


# ============================================================
# 3) Extrações úteis (NS/BM, data/hora, etc.)
# ============================================================
def derive_nsbm_from_any_screen(screens: Dict[str, str]) -> Optional[str]:
    """
    SERVIDOR:142924-0-... -> 1429240
    """
    for txt in screens.values():
        if not txt:
            continue
        m = re.search(r"SERVIDOR:\s*(\d{3,})-(\d)\b", txt)
        if m:
            return f"{m.group(1)}{m.group(2)}"
    return None


def extract_sigp_datetime(screens: Dict[str, str]) -> Optional[datetime]:
    """
    Pega PRODEMGE 06/02/2026 + SIGP 10:12:00 e monta datetime.
    """
    for txt in screens.values():
        if not txt:
            continue

        m_date = (
            re.search(r"PRODEMGE\s*0?(\d{2}/\d{2}/\d{4})", txt)
            or re.search(r"PRODEMGE\s*(\d{2}/\d{2}/\d{4})", txt)
        )
        m_time = re.search(r"\bSIGP\s+(\d{2}:\d{2}:\d{2})\b", txt)

        if m_date and m_time:
            try:
                return datetime.strptime(f"{m_date.group(1)} {m_time.group(1)}", "%d/%m/%Y %H:%M:%S")
            except ValueError:
                pass
    return None


def extract_servidor_unidade(screens: Dict[str, str]) -> Tuple[Optional[str], Optional[str]]:
    servidor = None
    unidade = None

    for txt in screens.values():
        if not txt:
            continue

        if not servidor:
            # Captura tudo após "SERVIDOR:" até o fim da linha
            m_serv = re.search(r"SERVIDOR:\s*(.+)", txt)
            if m_serv:
                raw = m_serv.group(1).strip()
                # Remove campos que vem depois (UNIDADE, NOME, etc.)
                # Corta antes de "UNIDADE" se aparecer na mesma linha
                cut = re.split(r"\s{2,}UNIDADE", raw)[0]
                servidor = re.sub(r"\s{2,}", " ", cut).strip()

        if not unidade:
            m_uni = re.search(r"UNIDADE\s*:\s*(.+)", txt)
            if m_uni:
                raw = m_uni.group(1).strip()
                # Corta antes de campos seguintes como DATA, NOME, etc.
                cut = re.split(r"\s{3,}(?:DATA|NOME|NUM|OPCAO)", raw)[0]
                unidade = re.sub(r"\s{2,}", " ", cut).strip()

        if servidor and unidade:
            break

    return servidor, unidade


# ============================================================
# 4) Layout / PDF
# ============================================================
def header_footer(canvas, doc, title: str, generated_dt: datetime):
    canvas.saveState()
    _, h = A4
    top = f"{title} • Gerado em {generated_dt.strftime('%d/%m/%Y %H:%M')} • Página {doc.page}"
    canvas.setFont("Helvetica", 9)
    canvas.drawString(18 * mm, h - 12 * mm, top)
    canvas.restoreState()


def _screen_box(story: List[Any], label: str, text: str, mono_style: ParagraphStyle):
    """
    Caixa alinhada (texto começa no início do quadro):
    - padding baixo
    - Preformatted mantém colunas fixas
    """
    label_style = ParagraphStyle("lbl", fontName="Helvetica", fontSize=10, spaceAfter=4)
    story.append(Paragraph(f"<b>{label}</b>", label_style))

    content = Preformatted(text, mono_style)

    # Ajuste fino: 170mm costuma caber bem com margens 18mm
    box = Table([[content]], colWidths=[170 * mm])
    box.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.8, colors.black),
                ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),

                # ✅ padding mínimo para "colar" no início do quadro
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    story.append(box)
    story.append(Spacer(1, 8))


def generate_pdf_from_screens(
    screens: Dict[str, str],
    output_dir: str | Path,
    nsbm_override: Optional[str] = None,
    max_cols: int = 92,
) -> Path:
    """
    Entrada:
      {
        "Tela IP": "...",
        "Tela DB": "...",
        "Tela FU": "...",
        "Tela FU 2": "..."
      }

    Regras:
      1) IP  -> Tela IP
      2) DB  -> Tela DB
      3) FU  -> Tela FU + Tela FU 2
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Normaliza + formata como terminal (colunas fixas)
    screens_norm: Dict[str, str] = {}
    for k, v in screens.items():
        txt = normalize_screen_text(v)
        txt = format_terminal_text(txt, max_cols=max_cols)
        screens_norm[k] = txt

    nsbm = nsbm_override or derive_nsbm_from_any_screen(screens_norm) or "SEM_REFERENCIA"
    sigp_dt = extract_sigp_datetime(screens_norm)
    servidor, unidade = extract_servidor_unidade(screens_norm)

    title = "EXTRATO DB FU IP"

    # Timestamp no nome: preferir data/hora da captura (SIGP); fallback para agora
    base_dt = sigp_dt if sigp_dt else datetime.now()
    timestamp = base_dt.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"EXTRATO DB FU IP _ {nsbm} _ {timestamp}.pdf"
    out_path = Path(output_dir) / filename

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleCenter",
        parent=styles["Title"],
        alignment=TA_CENTER,
        spaceAfter=8,
    )

    h_style = ParagraphStyle(
        "Heading2Tight",
        parent=styles["Heading2"],
        spaceBefore=10,
        spaceAfter=6,
    )

    # Mono: ajuste para caber melhor em A4
    mono_style = ParagraphStyle(
        "Mono",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=8.0,
        leading=9.5,
    )

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=16 * mm,
        title=title,
    )

    generated_dt = datetime.now()

    story: List[Any] = []
    story.append(Paragraph(title, title_style))

    # Metadados (SEM “Observação”)
    meta_rows = [
        ["Data/Hora da Captura (referência)", sigp_dt.strftime("%d/%m/%Y %H:%M") if sigp_dt else "-"],
        ["NS/BM (referência)", nsbm],
        ["Servidor (SIGP)", servidor or "-"],
        ["Unidade", unidade or "-"],
    ]

    meta_table = Table(meta_rows, colWidths=[65 * mm, 105 * mm])
    meta_table.setStyle(
        TableStyle(
            [
                ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # ===== Seções obedecendo exatamente os keys =====
    
    # 1) DB
    story.append(Paragraph("1) DB - Dados Basicos", h_style))
    db_text = screens_norm.get("Tela DB", "")
    if db_text.strip():
        _screen_box(story, "Tela DB", db_text, mono_style)
    else:
        story.append(Paragraph("Conteúdo 'Tela DB' não encontrado no dicionário.", styles["Italic"]))
        story.append(Spacer(1, 8))

    # 2) FU (Tela 1)
    story.append(Paragraph("2) FU - Cargos/Funcoes/Encargos Tela FU", h_style))
    fu_text = screens_norm.get("Tela FU", "")
    if fu_text.strip():
        _screen_box(story, "Tela FU", fu_text, mono_style)
    else:
        story.append(Paragraph("Conteúdo 'Tela FU' não encontrado no dicionário.", styles["Italic"]))
        story.append(Spacer(1, 8))

    # 3) IP
    story.append(Paragraph("3) IP - Informacao de Pagamento", h_style))
    ip_text = screens_norm.get("Tela IP", "")
    if ip_text.strip():
        _screen_box(story, "Tela IP", ip_text, mono_style)
    else:
        story.append(Paragraph("Conteúdo 'Tela IP' não encontrado no dicionário.", styles["Italic"]))
        story.append(Spacer(1, 8))

    # 4) FU (Tela 2)
    story.append(Paragraph("4) FU - Cargos/Funcoes/Encargos Tela FU 2", h_style))
    fu2_text = screens_norm.get("Tela FU 2", "")
    if fu2_text.strip():
        _screen_box(story, "Tela FU 2", fu2_text, mono_style)
    else:
        story.append(Paragraph("Conteúdo 'Tela FU 2' não encontrado no dicionário.", styles["Italic"]))
        story.append(Spacer(1, 8))

    doc.build(
        story,
        onFirstPage=lambda c, d: header_footer(c, d, title, generated_dt),
        onLaterPages=lambda c, d: header_footer(c, d, title, generated_dt),
    )

    return out_path


def merge_pdfs_in_folder(source_folder: str | Path, output_filename: str = "Anexo EXTRATO DB FU IP.pdf"):
    """
    Mescla todos os PDFs da pasta source_folder que terminam com .pdf 
    (exceto o próprio arquivo de saída se ele já existir lá)
    e salva como output_filename nessa mesma pasta.
    """
    source_path = Path(source_folder)
    writer = PdfWriter()
    
    # Listar todos os pdfs, ordenar se necessário (ex: por nome)
    if not source_path.exists():
        print(f"Pasta {source_folder} nao encontrada.")
        return

    # Pega apenas arquivos .pdf
    pdf_files = sorted([
        f for f in source_path.iterdir() 
        if f.is_file() and f.suffix.lower() == '.pdf' and f.name != output_filename
    ])

    if not pdf_files:
        print(f"Nenhum PDF encontrado em {source_folder} para mesclar.")
        return

    print(f"Encontrados {len(pdf_files)} PDFs para mesclar...")
    for pdf_file in pdf_files:
        try:
            writer.append(pdf_file)
            print(f" + Adicionado: {pdf_file.name}")
        except Exception as e:
            print(f" X Erro ao adicionar {pdf_file.name}: {e}")

    output_path = source_path / output_filename
    try:
        with open(output_path, "wb") as f_out:
            writer.write(f_out)
        print(f"PDF Unificado gerado com sucesso: {output_path}")
    except Exception as e:
        print(f"Erro ao salvar PDF unificado: {e}")

# --------- Exemplo de uso ----------
if __name__ == "__main__":
    telas_dict = {'Tela IP': 'N\nS99CBMMG -        SISTEMAGESTODEPESSOAS              PRODEMGE06/02/2026\n                                                SIGP    10:20:03\n INFORMACAO DE PAGAMENTO                 PESQUISA1\n                                              SERVIDOR:142924-0-CAP     -QOBM\n   -CLEYTON BATISTA DE JESUS      UNIDADE:000009405-DLF/SDTS2 TELECOMUNICACOES C\nHEFE ADJ AUX             DATA INFORMACAO DE PAGAMENTO :01/12/2025PERCENTUAL CORR\nECAO URV :      PASEP EM FOLHA (S/N) ? ..... :S            IND AUX. INVALIDEZ (S\n/N):      DATA ISENTO IMPOSTO DE RENDA :  /  /    DESCONTA IPSM (S/N) ? ..:S\n DATA IMUNE CONTRIBUICAO PREV.:  /  /    PERC. DESC. IPSM........:  8,00IND. GRA\nT. TRINT. ESP. (S/N) :N            VALOR DA QUOTA .........:      DATA ABONO PER\nMANENCIA     :  /  /    NUM. BASE APOSENTADORIA :      QUANTIDADE QUINQ. ADM/MAG\n  : /         ADIC.TRINTENARIO (S/N) .:      QTD. ADMIN. EM 01/01/2022  :\n      ADIC.TRINT EC59 (S/N) :      ARTIGO 71/EPPM (S/N)       :N            PERC\n.JUDICIAL/STF (S/N).:N     DATA ADICIONAL DESEMP. PAGT:21/02/2025COD. LIMINARES\nJUSTICA:      CODIGO TIPO BOLETIM        :4            PERCENTUAL ADIC. DESEMP :\n 30,00IND ABONO PERMANENCIA      :             NUMERO BOLETIM        :      ADE\nQOR/QPR DESIG.P/ATIV   :             UNIDADE BOLETIM       :      DATA ADE QOR/Q\nPR           :             ANO BOLETIM           :      NUMERO :      -  NOME\n                                                 OPCAO:___    MENU:__:\n                                       PF1- HELP   PF7- PRIMEIRA TELA      PF8-\nTELA POSTERIOR   PF12- SAIR', 'Tela DB': 'EXISTE MAIS UMA TELA PARA COMPLEMENTAR A PESQUISA -TECLE ENTER                 N\nS58CBMMG -        SISTEMAGESTODEPESSOAS              PRODEMGE06/02/2026\n                                                SIGP    10:20:07\n      DADOS BASICOS                      PESQUISA *21\n                                         SERVIDOR:142924-0-CAP     -QOBM      -C\nLEYTON BATISTA DE JESUS        UNIDADE :000009405-DLF/SDTS2 TELECOMUNICACOES CHE\nFE ADJ AUX\n                        NOME SERVIDOR .....:CLEYTON BATISTA DE JESUS\n                     NOME COMPLETO SERV.:CLEYTON BATISTA DE JESUS\n\n                 DATA NASCIMENTO ...:12/2 /1988        SEXO (F/M) .......:M\n       ESTADO CIVIL ......:1SOLTEIRO             NUMERO DO CONJUGE :      -0   N\nUM.REGISTRO GERAL :MG-19674285         ORGAO EMISSOR R.G.:SSP-MG       DATA EMIS\nSAO R.G...:19/4 /2012                                           NUM.TITULO ELEIT\nOR.:3471621301-41       SECAO216 ZONA :102          NUMERO CPF ........:087.617.\n246-02  NUMERO PIS/PASEP:1292809110-8DATA RECADASTRAMENTO:  /  /           CBO..\n.............:030205                                                   CODIGO AU\nTORIDADE.:             NUMERO:      -  NOME:\n               OPCAO:_-__ MENU:__\n\n     PF1- HELP                                                       PF12- SAIR', 'Tela FU': 'EXISTE MAIS UMA TELA PARA COMPLEMENTAR A PESQUISA -TECLE ENTER                 N\nS58CBMMG -        SISTEMAGESTODEPESSOAS              PRODEMGE06/02/2026\n                                                SIGP    10:20:07\n      DADOS BASICOS                      PESQUISA *21\n                                         SERVIDOR:142924-0-CAP     -QOBM      -C\nLEYTON BATISTA DE JESUS        UNIDADE :000009405-DLF/SDTS2 TELECOMUNICACOES CHE\nFE ADJ AUX\n                        NOME PAI ..........:CARLOS DE JESUS\n                     NOME COMPLETO PAI..:CARLOS DE JESUS\n\n                 NOME MAE ..........:MARIA DO ROSARIO BATISTA DE JESUS\n              NOME COMPLETO MAE..:MARIA DO ROSARIO BATISTA DE JESUS\n\n          NUM.BANCO / AGENCIA:341/7958   -BELO HORIZONTE-SHOPPICONTA :12725   5D\nEP. ABONO FAMILIA :                         DEP. IMPOSTO RENDA :         CODIGO\nFALECIMENTO :                                                         NUMERO BOL\nETIM .....:    ANO BOLETIM :    UNIDADE BOLETIM ...:\n\n                                                           NUMERO:      -  NOME:\n                                                   OPCAO:P-FU MENU:__\n\n                                         PF1- HELP\n                         PF12- SAIR', 'Tela FU 2': "N\nR65CBMMG -         SISTEMAGESTODEPESSOAS           PRODEMGE  06/02/2026\n                                                  SIGP  S142924        CARGOS/FU\nNCOES/ENCARGOS DO SERVIDOR            PESQUISA\n                                                SERVIDOR:142924-0-CAP     -QOBM\n     -CLEYTON BATISTA DE JESUS       UNIDADE :000009405-DLF/SDTS2 TELECOMUNICACO\nES CHEFE ADJ AUX\n                               DATA DE INICIO.........: <18/04/2024>     TIPO BO\nLETIM NOMEACAO :4                                                     NUM BOLETI\nM ........:    DATA DE TERMINO........: <00/00/0000>       ANO BOLETIM ........:\n                                                      UNIDADE BOLETIM ....:    T\nIPO LOCAL ...............:956                                             DESC L\nOCAL ...............:GERENCIA DE SISTEMAS                            CODIGO CARG\nO .............:828                                             DESC CARGO .....\n..........:GERENTE LOSG                                    E' ENCARGO (S/N) ....\n.....:S                                               ORGAO PRESTACAO SERVICO ..\n:DLF/SDTS2 TELECOM CH                            PASSAGEM/RECEBIMENTO .....:\n                                            SERVIDOR PASSAGEM ........:\n\n\n\n                                                      ENTER- CONTINUAR PF12- MEN\nU PRINCIPAL"}

    pdf = generate_pdf_from_screens(telas_dict, output_dir="./saida_extratos", max_cols=92)
    print("PDF gerado:", pdf)
