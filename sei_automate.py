from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep
import os
import re
import json
from urllib.parse import urljoin
from dotenv import load_dotenv
import requests

load_dotenv()

# Configurar proxy para ignorar localhost (resolver problema com proxy Prodemge)
os.environ['NO_PROXY'] = 'localhost,127.0.0.1'
os.environ['no_proxy'] = 'localhost,127.0.0.1'

def muda_frame(navegador, id_frame, wait):
    """
    Função para mudar o frame do navegador para um frame específico pelo ID.
    """
    try:
        navegador.switch_to.default_content()
        ifr_vis = wait.until(
            EC.presence_of_element_located((By.ID, f"{id_frame}"))
        )
        navegador.switch_to.frame(ifr_vis)
        
        print(f"Mudou para {id_frame}")

    except Exception as frame_err:
        print(f"Falha ao acessar {id_frame}: {frame_err}")

def gerador_documento(navegador, conteudo_html, tipo_documento="Ofício", wait=None):
    """
    Função para gerar um documento a partir de um conteúdo HTML.
    """
    print("Entrando no gerador de documentos...")
     # mudar o frame
    muda_frame(navegador, "ifrVisualizacao", wait)
    print("Incluindo documento...")

    # cliar em Incluir Documento
    navegador.execute_script('document.querySelector("#divArvoreAcoes > a:nth-child(1) > img").click()')

    print("Documento incluído!")
    
    # Clica na ferramenta expansão
    navegador.find_element(By.CSS_SELECTOR, "#ancExibirSeries").click()
    
    # clicar em Ofício
    sleep(1)  # Aumentado para headless
    
    # Escreve o conteudo de tipo_documento no console para debug
    print(f"Selecionando tipo de documento: {tipo_documento}")
    


    ActionChains(navegador).send_keys(tipo_documento).perform()
    
    # Tecla tab
    ActionChains(navegador).send_keys(Keys.TAB).perform()
    sleep(0.5)  # Aumentado para headless
    
    # Tecla Enter
    ActionChains(navegador).send_keys(Keys.ENTER).perform()
    

    print(f"Tipo {tipo_documento} selecionado!")

    sleep(2)  # Aumentado para headless
    # clicar em Público
    navegador.execute_script('document.querySelector("#divOptPublico > div > label").click()')
    sleep(1)  # Aumentado para headless

    # clicar em Salvar
    navegador.execute_script('document.querySelector("#btnSalvar").click()')
    
    print(f"{tipo_documento} salvo!")
    
    sleep(12)  # Aumentado para headless - aguardar nova janela abrir

    # mudar a janela - esperar até ter 2 janelas
    wait = WebDriverWait(navegador, 20)
    wait.until(lambda d: len(d.window_handles) > 1)
    
    janela2 = navegador.window_handles[1]
    navegador.switch_to.window(janela2)
    
    sleep(2)  # Aguardar janela carregar completamente

    print("Inserindo conteúdo no editor...")

    # mudar o iframe - aguardar estar presente
    try:
        iframe = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#cke_3_contents > iframe")))
        navegador.switch_to.frame(iframe)
        print("Mudou para iframe do editor")
    except Exception as iframe_err:
        print(f"Falha ao acessar iframe do editor: {iframe_err}")
        return
    
    sleep(1)  # Aguardar iframe carregar
    try:
        # Aguarda o body estar presente
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
        print("Editor pronto para receber conteúdo")
        navegador.execute_script(f"document.body.innerHTML = `{conteudo_html}`")
    except Exception as body_err:
        print(f"Falha ao acessar body do editor: {body_err}")
        return
    #cke_3_contents > iframe
    
    return
    
    sleep(1)  # Aguardar conteúdo ser inserido
    
    print("Conteúdo inserido no ofício!")

    # salvar o documento
    navegador.switch_to.default_content()
    sleep(2)
    
    # Clicar no botão salvar com wait
    btn_salvar = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/div[1]/div[1]/div/div/span[2]/span[1]/span[3]/a")))
    navegador.execute_script("arguments[0].click();", btn_salvar)
    
    print("Salvando documento...")
    
    sleep(3)  # Aumentado para headless
    navegador.close()
    
    print("Documento salvo!")
    

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
            "ct": ct,
            "details": {}
        }
    
    return militares


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


def acessar_texto_body(navegador, wait):
    # Aguarda o conteúdo carregar antes de mudar de frame
    sleep(2)
    # Muda para o frame visualização
    navegador.switch_to.default_content()
    ifr_vis = wait.until(
        EC.presence_of_element_located((By.ID, "ifrVisualizacao"))
    )
    navegador.switch_to.frame(ifr_vis)
    print("Mudou para ifrVisualizacao")
    
    ifr_vis = wait.until(
        EC.presence_of_element_located((By.ID, "ifrArvoreHtml"))
    )
    navegador.switch_to.frame(ifr_vis)
    print("Mudou para ifrArvoreHtml")
    
    # Aguarda o conteúdo do documento carregar
    element = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
    )
    
    texto = element.text

    return texto

def gerar_resposta(doc_sei):
    try:
        print("Iniciando processo...")
        
        # Definição de Variaveis
        options = webdriver.ChromeOptions()
        
        # options.add_argument('--headless=new')
        
        # Argumentos adicionais para headless funcionar melhor
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--window-size=1920,1080')
        
        # Desabilitar proxy completamente (resolver problema com proxy Prodemge)
        options.add_argument('--no-proxy-server')
        options.add_argument("--proxy-server='direct://'")
        options.add_argument('--proxy-bypass-list=*')
        
        # Configurações para evitar detecção de automação
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Preferências adicionais
        DOWNLOAD_DIR = os.path.abspath("downloads")
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        
        prefs = {
            "download.default_directory": DOWNLOAD_DIR,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,  # força baixar PDF ao invés de abrir no viewer
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
        }
        options.add_experimental_option("prefs", prefs)

        servico = Service(ChromeDriverManager().install())
        navegador = webdriver.Chrome(service=servico, options=options)
        navegador.implicitly_wait(10)
        wait = WebDriverWait(navegador, 20)
        user_agent = navegador.execute_script("return navigator.userAgent;")

        user = os.getenv("USER_SEI")
        password = os.getenv("PASSWORD_SEI")
        orgao = os.getenv("ORGAO")

        print("Acessando o sistema SEI...")
        
        # acessa o site do SEI
        navegador.get("https://www.sei.mg.gov.br/")
        
        # Não precisa de maximize_window no headless (já definido no window-size)

        # inserir o meu usuário
        navegador.find_element(By.ID, "txtUsuario").send_keys(user)
        sleep(0.5)

        # inserir minha senha
        navegador.find_element(By.ID, "pwdSenha").send_keys(password)

        # inserir o orgao
        select_element = navegador.find_element(By.ID, "selOrgao")
        select = Select(select_element)
        select.select_by_visible_text(orgao)

        # clicar no botão acessar
        navegador.find_element(By.ID, "Acessar").click()

        print("Login realizado com sucesso!")
        print("Varredura de documentos existentes...")
        
        # clicar em Pesquisar
        pesquisa = navegador.find_element(By.ID, "txtPesquisaRapida")
        pesquisa.send_keys(doc_sei)
        pesquisa.send_keys(Keys.ENTER)
        print('pesquisou')
        
        # mudar o frame
        iframe = navegador.find_element(By.ID, "ifrArvore")
        navegador.switch_to.frame(iframe)
        print('mudou para o frame ifrArvore')
        sleep(1)
        
        arvore_pross = navegador.find_element(By.ID, "divArvore")
        print('encontrou a arvore')
        
        elementos = arvore_pross.find_elements(By.CSS_SELECTOR, 'div > a[target="ifrVisualizacao"] > span')
        
        print("Quantidade de elemento encontrados na árvore:", len(elementos))
        
        # lista com os textos visíveis
        
        rel_viagem_det = None
        rels_viagem_dil = []

        docs_arvore = []
        for el in elementos:
            texto = el.text.strip()
            if not texto:
                continue
            if "Viagem/Determinação da DSP" in texto:
                rel_viagem_det = el
            if "Viagem/Diligente" in texto:
                
                span_id = (el.get_attribute("id") or "").strip()
                if span_id.startswith("span"):
                    span_id = span_id.replace("span", "", 1)
                rels_viagem_dil.append([el, span_id, texto])
                
                

            span_id = (el.get_attribute("id") or "").strip()
            if span_id.startswith("span"):
                span_id = span_id.replace("span", "", 1)

            docs_arvore.append([span_id, texto])

        print(docs_arvore)
        
        print(f"Relatórios de Viagem: {rels_viagem_dil}")
        
        links_pdf = navegador.find_elements(By.CSS_SELECTOR, "img[src*='pdf']")
        
        print(f"O numero de elementos encontrado é: {len(links_pdf)}")

        pdf_anchors = []
        prox_anchors = []

        for img in links_pdf:
            try:
                anchor = img.find_element(By.XPATH, "./ancestor::a[1]")
                pdf_anchors.append(anchor)
                prox_anchor = anchor.find_element(By.XPATH, "following-sibling::a[1]")
                prox_anchors.append(prox_anchor)
            except Exception as err:
                print(f"Falha ao capturar âncoras relacionadas ao PDF: {err}")

        print(f"Âncoras com PDF encontradas: {len(pdf_anchors)}")
        print(f"Próximas âncoras encontradas: {len(prox_anchors)}")

        links_baixados = set()

        def baixar_arquivo_relacionado(href, indice, nome_arquivo=None):
            if not href or href == "(sem href)":
                print(f"[{indice}] href inválido para download")
                return

            download_url = urljoin("https://www.sei.mg.gov.br/sei/", href)
            print(f"[{indice}] preparando download: {download_url}")

            try:
                session = requests.Session()
                for cookie in navegador.get_cookies():
                    session.cookies.set(
                        cookie["name"],
                        cookie["value"],
                        domain=cookie.get("domain"),
                        path=cookie.get("path"),
                    )

                headers = {
                    "Referer": navegador.current_url,
                    "User-Agent": user_agent,
                }

                response = session.get(download_url, headers=headers, timeout=60, stream=True)
                response.raise_for_status()

                content_disposition = response.headers.get("content-disposition", "")
                content_type = response.headers.get("content-type", "")

                if "pdf" not in content_type.lower():
                    snippet = response.text[:200]
                    print(f"[{indice}] conteúdo inesperado ({content_type}): {snippet}")
                    return

                if nome_arquivo:
                    filename = f"{nome_arquivo}.pdf"
                else:
                    filename = None
                    match = re.search(r'filename="?([^";]+)"?', content_disposition)
                    if match:
                        filename = match.group(1)
                    if not filename:
                        filename = f"sei_download_{indice}.pdf"

                destino = os.path.join(DOWNLOAD_DIR, filename)
                with open(destino, "wb") as arquivo_saida:
                    for chunk in response.iter_content(chunk_size=8192):
                        if not chunk:
                            continue
                        arquivo_saida.write(chunk)

                print(f"[{indice}] download concluído em {destino}")
            except Exception as download_err:
                print(f"[{indice}] falha no download: {download_err}")

        def processar_links_de_anexo(indice, id_documento=None):
            try:
                anexos = navegador.find_elements(
                    By.CSS_SELECTOR,
                    "a.ancoraVisualizacaoArvore[href*='documento_download_anexo']",
                )
            except Exception as captura_err:
                print(f"[{indice}] falha ao procurar links de anexo: {captura_err}")
                return

            if not anexos:
                print(f"[{indice}] nenhum anexo disponível para download")
                return

            for posicao, link in enumerate(anexos, start=1):
                href = link.get_attribute("href")
                if not href:
                    continue

                if href in links_baixados:
                    print(f"[{indice}] anexo já baixado, ignorando")
                    continue

                links_baixados.add(href)
                descricao = link.text.strip() or f"anexo_{posicao}"
                print(f"[{indice}] anexo identificado ({descricao})")
                baixar_arquivo_relacionado(href, f"{indice}_{posicao}", nome_arquivo=id_documento)

        for idx, (anchor, prox_anchor) in enumerate(zip(pdf_anchors, prox_anchors), start=1):
            atual = anchor.get_attribute("href") or "(sem href)"
            proximo = prox_anchor.get_attribute("href") or "(sem href)"

            # Extrair id_documento da URL do próximo elemento
            id_doc_match = re.search(r'id_documento=(\d+)', proximo)
            id_documento = id_doc_match.group(1) if id_doc_match else None

            print(f"[{idx}] href atual: {atual}")
            print(f"[{idx}] href próximo: {proximo}")
            print(f"[{idx}] id_documento: {id_documento}")

            # Garantir que o próximo elemento esteja visível e clicar nele
            try:
                navegador.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});",
                    prox_anchor,
                )
                navegador.execute_script("arguments[0].click();", prox_anchor)
                print(f"[{idx}] clique no elemento próximo efetuado")
            except Exception as click_err:
                print(f"[{idx}] falha ao clicar no elemento próximo: {click_err}")
                continue

            # Voltar ao contexto principal e entrar no ifrVisualizacao
            # (o clique na árvore carrega o documento nesse iframe)
            navegador.switch_to.default_content()
            sleep(2)

            try:
                ifr_vis = wait.until(
                    EC.presence_of_element_located((By.ID, "ifrVisualizacao"))
                )
                navegador.switch_to.frame(ifr_vis)
                print(f"[{idx}] mudou para ifrVisualizacao")

                # Aguardar o link de download do anexo aparecer
                sleep(2)
                processar_links_de_anexo(idx, id_documento=id_documento)

            except Exception as frame_err:
                print(f"[{idx}] falha ao acessar ifrVisualizacao: {frame_err}")

            # Voltar para ifrArvore para a próxima iteração
            navegador.switch_to.default_content()
            iframe_arvore = navegador.find_element(By.ID, "ifrArvore")
            navegador.switch_to.frame(iframe_arvore)
            print(f"[{idx}] voltou para ifrArvore")

            sleep(1)
        try:
            print("Iniciando leitura de relatórios relacionados...")
            # Buscar documento e conteudos na arvore do sei
            # 1 - Encontrar documento chamado "CBMMG - Rel. Viagem/Determinação da DSP"
            
            # Garante que está no contexto correto do frame ifrArvore
            navegador.switch_to.default_content()
            iframe_arvore = navegador.find_element(By.ID, "ifrArvore")
            navegador.switch_to.frame(iframe_arvore)
            print('voltou para ifrArvore')
            
            arvore_pross = navegador.find_element(By.ID, "divArvore")
            print('encontrou a arvore')
            
            rel_viagem_det.click()
            print("Clique no relatório de viagem/determinação da DSP efetuado")
            
            # Aguarda o conteúdo carregar antes de mudar de frame
            texto = acessar_texto_body(navegador, wait)
            print(texto)
            
            # Extrai os dados dos militares da tabela
            print("\n" + "="*50)
            print("Extraindo dados dos militares...")
            militares_dict = extrair_militares_relatorio(texto)
            
            print(f"Total de militares encontrados: {len(militares_dict)}")
            
            # Exibe os dados extraídos
            print("\nDados extraídos:")
            print(json.dumps(militares_dict, indent=2, ensure_ascii=False))
            
            # Iterar sobre todos os relatorios de viagem dos militares
            for rel in rels_viagem_dil:
                try:
                    # Garante que está no contexto correto do frame ifrArvore
                    navegador.switch_to.default_content()
                    iframe_arvore = navegador.find_element(By.ID, "ifrArvore")
                    navegador.switch_to.frame(iframe_arvore)
                    print('voltou para ifrArvore')
                    sleep(1)
                    
                    arvore_pross = navegador.find_element(By.ID, "divArvore")
                    print('encontrou a arvore')
                    sleep(1)
                    
                    rel[0].click()
                    print("Clique no relatório de viagem/determinação da DSP efetuado")
                    sleep(1)
                    
                    texto = acessar_texto_body(navegador, wait)
                    print("Texto de relatorio de viagem/diligente:")
                    print(texto)
                    
                    # Extrai os detalhes de viagem e encontra o militar correspondente
                    num_militar, detalhes_viagem = extrair_detalhes_viagem(texto)
                    
                    if num_militar and detalhes_viagem:
                        # Procura o militar no dicionário pelo número militar
                        for key, militar in militares_dict.items():
                            if militar.get("numero") == num_militar:
                                # Adiciona os detalhes da viagem ao militar
                                militar["details"] = detalhes_viagem
                                print(f"\n✓ Detalhes de viagem adicionados ao militar {num_militar} (chave {key})")
                                print(json.dumps(detalhes_viagem, indent=2, ensure_ascii=False))
                                break
                        else:
                            print(f"\n⚠ Militar {num_militar} não encontrado no dicionário")
                    else:
                        if not num_militar:
                            print("\n⚠ Número militar não encontrado no relatório")
                        if not detalhes_viagem:
                            print("\n⚠ Detalhes de viagem não encontrados no relatório")
                    
                except Exception as rel_err:
                    print(f"Erro ao processar relatório de viagem/diligente: {rel_err}")
            
            # Exibe o dicionário completo com todos os detalhes adicionados
            print("\n" + "="*70)
            print("DICIONÁRIO COMPLETO DE MILITARES COM DETALHES DE VIAGEM:")
            print("="*70)
            print(json.dumps(militares_dict, indent=2, ensure_ascii=False))
            print("="*70)
            
            # Criando os documentos para compor a arvore do processo
            conteudo_doc = "<h1>Teste para conteudo de documento</h1><p>Gerado automaticamente pelo script de automação.</p>"
            gerador_documento(navegador,conteudo_doc, "Viagem/Agente de Ação", wait)
            
            try:
                print("Criando documentos para compor a árvore do processo...")
            except Exception as doc_err:
                print(f"Erro na criação de documentos: {doc_err}")
            
        except Exception as expand_err:
            print("Erro na leitura de relatórios")
            print(f"Falha ao expandir conteúdo relacionado: {expand_err}")

            
            

        sleep(1000)  # Aumentado para headless - aguardar página carregar

        return
        
    except Exception as e:
        print(f"❌ ERRO: {str(e)}", "error")
        try:
            navegador.quit()
        except:
            pass


if __name__ == "__main__":
    # Documento Base do CEB
    
    documento_sei = "1400.01.0008514/2026-81"
    gerar_resposta(documento_sei)
    
    
