import re
import json

def extrair_detalhes_viagem(texto):
    """
    Extrai os detalhes de viagem (partida/destino) do relatório de viagem individual.
    Retorna o número militar e um dicionário com os detalhes das viagens.
    """
    detalhes = {}
    num_militar = None
    
    # Extrai o número militar
    num_militar_match = re.search(r'N\.\s*MILITAR:\s*:?\s*\n?\s*(\d{3}\.\d{3}-\d)', texto)
    if num_militar_match:
        num_militar = num_militar_match.group(1)
    
    # Extrai as linhas de viagem
    linhas = texto.split('\n')
    
    # Encontra o índice onde começa a tabela de viagens
    inicio_tabela = -1
    for i, linha in enumerate(linhas):
        if 'LOCAL DE PARTIDA' in linha and 'LOCAL DE DESTINO' in linha:
            inicio_tabela = i + 1
            break
    
    if inicio_tabela == -1:
        return num_militar, detalhes
    
    # Processa as linhas seguintes para extrair detalhes
    i = inicio_tabela
    while i < len(linhas):
        linha = linhas[i].strip()
        
        # Verifica se chegou na seção de observações ou fim da tabela
        if 'OBSERVAÇÕES' in linha or 'Referência:' in linha or 'Criado por' in linha:
            break
            
        # Verifica se é uma linha com número de sequência (01, 02, etc)
        if re.match(r'^\d{2}$', linha):
            num_seq = linha
            
            # As próximas linhas contêm os dados
            try:
                l_partida = linhas[i + 1].strip() if i + 1 < len(linhas) else ""
                d_partida = linhas[i + 2].strip() if i + 2 < len(linhas) else ""
                h_partida = linhas[i + 3].strip() if i + 3 < len(linhas) else ""
                l_destino = linhas[i + 4].strip() if i + 4 < len(linhas) else ""
                d_destino = linhas[i + 5].strip() if i + 5 < len(linhas) else ""
                h_destino = linhas[i + 6].strip() if i + 6 < len(linhas) else ""
                
                # Verifica se os dados são válidos (não vazios e não são números de sequência ou observações)
                # Para ser válido, precisa ter ao menos local de partida que não seja número e uma data
                if (l_partida and 
                    not re.match(r'^\d{2}$', l_partida) and 
                    'OBSERVAÇÕES' not in l_partida and
                    d_partida and 
                    re.match(r'\d{2}/\d{2}/\d{4}', d_partida)):  # Valida formato de data
                    detalhes[num_seq] = {
                        "l_partida": l_partida,
                        "d_partida": d_partida,
                        "h_partida": h_partida,
                        "l_destino": l_destino,
                        "d_destino": d_destino,
                        "h_destino": h_destino
                    }
                    i += 7  # Pula para a próxima entrada
                else:
                    i += 1  # Pula apenas uma linha se não for válido
            except IndexError:
                break
        else:
            i += 1
    
    return num_militar, detalhes


# Texto de exemplo do teste.txt
texto_exemplo = """GOVERNO DO ESTADO DE MINAS GERAIS
CORPO DE BOMBEIROS MILITAR DE MINAS GERAIS
Subdiretoria de Tecnologia e Sistemas
  Belo Horizonte, 09 de fevereiro de 2026.
   RELATÓRIO DE VIAGEM CBMMG
CBMMG-RELATÓRIO DE VIAGEM/DADOS DO LOCAL,DATAS E HORÁRIOS
ORIGEM DA DSP (O.S/B.O):
2025-058984040-001
UNIDADE DO MILITAR:
BOA
N. MILITAR: :
167.493-6
NOME:
João Paulo do Carmo Souza
POSTO/GRAD:
1° Tenente
N° Seq. LOCAL DE PARTIDA DATA DE PARTIDA HORÁRIO DE PARTIDA LOCAL DE DESTINO DATA DE DESTINO HORÁRIO DE DESTINO
01
Belo horizonte
23/12/2025
10:01
Teófilo Otoni
23/12/2025
11:24
02
Teófilo Otoni
23/12/2025
13:39
Uberlândia
23/12/2025
16:00
03
Uberlândia
23/12/2025
16:54
Belo horizonte
23/12/2025
18:34
04
05
06
07
08
09
10
OBSERVAÇÕES DA DSP:
  DSP TRANSCORREU SEM ALTERAÇÕES.
    Referência: Processo nº 1400.01.0008514/2026-81 SEI nº 132918758
Criado por 08761724602, versão 1 por 08761724602 em 09/02/2026 13:30:28."""

# Dicionário de exemplo de militares
militares_dict = {
    "01": {
        "unidade": "BOA",
        "cpf": "123.456.789-00",
        "numero": "167.493-6",
        "nome": "João Paulo do Carmo Souza",
        "posto_grad": "1° Tenente",
        "sede": "Belo Horizonte - MG",
        "destinos": "Teófilo Otoni/Uberlândia",
        "di": "2",
        "pa_pp": "1",
        "mpa": "-"
    },
    "02": {
        "unidade": "BOA",
        "cpf": "987.654.321-00",
        "numero": "123.456-7",
        "nome": "Maria Silva Santos",
        "posto_grad": "Capitão",
        "sede": "Belo Horizonte - MG",
        "destinos": "Uberlândia",
        "di": "1",
        "pa_pp": "-",
        "mpa": "-"
    }
}

print("="*70)
print("TESTE DE EXTRAÇÃO DE DETALHES DE VIAGEM")
print("="*70)
print("\nMilitares_dict antes da extração:")
print(json.dumps(militares_dict, indent=2, ensure_ascii=False))

# Extrai os detalhes
num_militar, detalhes_viagem = extrair_detalhes_viagem(texto_exemplo)

print("\n" + "="*70)
print(f"Número militar extraído: {num_militar}")
print("\nDetalhes de viagem extraídos:")
print(json.dumps(detalhes_viagem, indent=2, ensure_ascii=False))

# Adiciona os detalhes ao militar correspondente
if num_militar and detalhes_viagem:
    for key, militar in militares_dict.items():
        if militar.get("numero") == num_militar:
            militar["details"] = detalhes_viagem
            print("\n" + "="*70)
            print(f"✓ Detalhes adicionados ao militar {num_militar} (chave {key})")
            break
    else:
        print(f"\n⚠ Militar {num_militar} não encontrado no dicionário")

print("\n" + "="*70)
print("MILITARES_DICT DEPOIS DA EXTRAÇÃO:")
print("="*70)
print(json.dumps(militares_dict, indent=2, ensure_ascii=False))
