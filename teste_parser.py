import json
import re

def extrair_militares_relatorio(texto):
    """
    Extrai informações dos militares da tabela do relatório de viagem.
    Retorna um dicionário de dicionários com os dados de cada militar.
    """
    militares = {}
    
    # Procura por linhas que começam com número (01, 02, 03, etc)
    # Padrão: NUM UNIDADE CPF N.MILITAR NOME POSTO/GRAD VANTAGENS SEDE DESTINO DIST DIARIAS BANCO AG CONTA
    padrao = r'^(\d{2})\s+(\w+)\s+(\d{3}\.\d{3}\.\d{3}-\d{2})\s+(\d{3}\.\d{3}-\d)\s+([\w\s]+?)\s+((?:Capitão|Tenente|Major|Coronel|1° Tenente|2° Tenente|Sargento|Cabo|Soldado|Subtenente))\s+(.+)$'
    
    linhas = texto.split('\n')
    
    for linha in linhas:
        linha = linha.strip()
        if not linha:
            continue
            
        # Tenta encontrar linha que começa com número seguido de unidade
        match = re.match(r'^(\d{2})\s+(\w+)\s+(.+)$', linha)
        if not match:
            continue
            
        num_seq = match.group(1)
        unidade = match.group(2)
        resto = match.group(3)
        
        # Parse do resto da linha (CPF, N.MILITAR, NOME, etc)
        # CPF: XXX.XXX.XXX-XX
        cpf_match = re.search(r'(\d{3}\.\d{3}\.\d{3}-\d{2})', resto)
        if not cpf_match:
            continue
        cpf = cpf_match.group(1)
        resto = resto[cpf_match.end():].strip()
        
        # N. MILITAR: XXX.XXX-X
        num_militar_match = re.search(r'^(\d{3}\.\d{3}-\d)', resto)
        if not num_militar_match:
            continue
        num_militar = num_militar_match.group(1)
        resto = resto[num_militar_match.end():].strip()
        
        # NOME e POSTO/GRAD (procura pelo posto/grad conhecido)
        posto_grad_pattern = r'(Capitão|Tenente|Major|Coronel|1° Tenente|2° Tenente|Sargento|Cabo|Soldado|Subtenente|General)'
        posto_match = re.search(posto_grad_pattern, resto)
        if not posto_match:
            continue
        nome = resto[:posto_match.start()].strip()
        posto_grad = posto_match.group(1)
        resto = resto[posto_match.end():].strip()
        
        # VANTAGENS: - QQ ADE% (ex: - 30 significa ADE=30)
        # Padrão geralmente: - NUM ou NUM - -
        partes_vantagem = resto.split(None, 3)  # Divide em até 4 partes
        qq = ""
        ade = ""
        perc = ""
        
        if len(partes_vantagem) >= 3:
            # Ex: "- 30 Belo Horizonte..."
            if partes_vantagem[0] == "-":
                qq = ""
                ade = partes_vantagem[1] if partes_vantagem[1] != "-" else ""
                resto = " ".join(partes_vantagem[2:])
            else:
                resto = " ".join(partes_vantagem)
        
        # SEDE: geralmente "Cidade - UF"
        sede_match = re.search(r'([A-Za-zÀ-ú\s]+\s*-\s*[A-Z]{2})', resto)
        if not sede_match:
            continue
        sede = sede_match.group(1).strip()
        resto = resto[sede_match.end():].strip()
        
        # DESTINO(S): próxima cidade com UF ou composto com /
        destino_match = re.search(r'([A-Za-zÀ-ú\s/]+(?:\s*-\s*[A-Z]{2})?)', resto)
        destino = destino_match.group(1).strip() if destino_match else ""
        if destino_match:
            resto = resto[destino_match.end():].strip()
        
        # DISTÂNCIA: XXX km
        dist_match = re.search(r'(\d+\s*km)', resto)
        dist = dist_match.group(1) if dist_match else ""
        if dist_match:
            resto = resto[dist_match.end():].strip()
        
        # DIÁRIAS: - DI PA/PP ½PA (ex: "- 1 -" ou "1 - -")
        partes_diarias = resto.split(None, 3)
        di = ""
        pa_pp = ""
        mpa = ""
        
        if len(partes_diarias) >= 3:
            di = partes_diarias[0] if partes_diarias[0] != "-" else ""
            pa_pp = partes_diarias[1] if partes_diarias[1] != "-" else ""
            mpa = partes_diarias[2] if partes_diarias[2] != "-" else ""
            if len(partes_diarias) > 3:
                resto = partes_diarias[3]
            else:
                resto = ""
        
        # BANCO: nome - código
        banco_match = re.search(r'([A-Za-zÀ-ú\s]+-\s*\d+)', resto)
        banco = banco_match.group(1).strip() if banco_match else ""
        if banco_match:
            resto = resto[banco_match.end():].strip()
        
        # AGÊNCIA e CONTA: últimos números
        partes_finais = resto.split()
        ag = partes_finais[0] if len(partes_finais) > 0 else ""
        ct = partes_finais[1] if len(partes_finais) > 1 else ""
        
        militares[num_seq] = {
            "unidade": unidade,
            "cpf": cpf,
            "numero": num_militar,
            "nome": nome,
            "posto_grad": posto_grad,
            "qq": qq,
            "ade": ade,
            "perc": perc,
            "sede": sede,
            "destinos": destino,
            "dist": dist,
            "di": di,
            "pa_pp": pa_pp,
            "mpa": mpa,
            "banco": banco,
            "ag": ag,
            "ct": ct
        }
    
    return militares


# Texto de exemplo fornecido pelo usuário
texto_exemplo = """GOVERNO DO ESTADO DE MINAS GERAIS
CORPO DE BOMBEIROS MILITAR DE MINAS GERAIS
Subdiretoria de Tecnologia e Sistemas
  Belo Horizonte, 09 de fevereiro de 2026.
   RELATÓRIO DE VIAGEM CBMMG
CBMMG-RELATÓRIO DE VIAGEM/AUTORIZAÇÃO PARA A DSP
ORIGEM DA DSP (O.S/B.O):
2025-058984040-001
N° Seq. UNIDADE CPF N. MILITAR NOME POSTO/GRAD VANTAGEM LOCAIS DISTÂNCIA PREVISÃO DE DIARIAS DILIGÊNCIA
N. QQ ADE % SEDE DESTINO(S) DI PA/PP ½ PA BANCO AGÊNCIA CONTA
01 BOA 047.600.536-11 147.857-7 Bruno França Gonçalves  Capitão - 30 Belo Horizonte - MG Teófilo Otoni/Uberlândia 441 km - 1 - Itaú - 341 6662 05749-3
02 BOA 071.036.086-01 167.493-6 João Paulo do Carmo Souza 1° Tenente - 10 Belo Horizonte - MG Teófilo Otoni/Uberlândia 441 km - 1 - Itaú - 104 6662 11685-1
03 BOA 140.913.917-45 164.065-5 Rafael de Oliveira Victoriano Cabo - 20 Belo Horizonte - MG Teófilo Otoni/Uberlândia 441 km - 1 - Bradesco-237 1056 38.291-4
Referência: Processo nº 1400.01.0008514/2026-81 SEI nº 132918392
Criado por 08761724602, versão 1 por 08761724602 em 09/02/2026 13:28:18."""

print("Testando extração de militares...")
resultado = extrair_militares_relatorio(texto_exemplo)

print(f"\nTotal de militares encontrados: {len(resultado)}")
print("\nResultado:")
print(json.dumps(resultado, indent=2, ensure_ascii=False))
