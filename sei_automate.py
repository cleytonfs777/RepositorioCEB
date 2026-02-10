from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from time import sleep
import os
from dotenv import load_dotenv

from dotenv import load_dotenv

load_dotenv()

# Configurar proxy para ignorar localhost (resolver problema com proxy Prodemge)
os.environ['NO_PROXY'] = 'localhost,127.0.0.1'
os.environ['no_proxy'] = 'localhost,127.0.0.1'


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
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
        }
        options.add_experimental_option("prefs", prefs)

        servico = Service(ChromeDriverManager().install())
        navegador = webdriver.Chrome(service=servico, options=options)
        navegador.implicitly_wait(10)

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

        docs_arvore = []
        for el in elementos:
            texto = el.text.strip()
            if not texto:
                continue

            span_id = (el.get_attribute("id") or "").strip()
            if span_id.startswith("span"):
                span_id = span_id.replace("span", "", 1)

            docs_arvore.append([span_id, texto])

        print(docs_arvore)
        
        sleep(100)  # Aumentado para headless - aguardar página carregar

        return
        
        print("Conteúdo encontrado! Gerando resposta com IA...")


        print("Resposta gerada pela IA!")
        print("Criando ofício...")


        print("Mudando para frame padrão...")
        
        # voltar para o frame padrão
        navegador.switch_to.default_content()

        # clicar em Pesquisar
        pesquisa = navegador.find_element(By.ID, "txtPesquisaRapida")
        pesquisa.send_keys(123456)
        pesquisa.send_keys(Keys.ENTER)

        print(f"Processo {123456} encontrado!")

        sleep(1)
        # mudar o frame
        iframe = navegador.find_element(By.ID, "ifrVisualizacao")
        navegador.switch_to.frame(iframe)
        sleep(1)

        print("Incluindo documento...")

        # cliar em Incluir Documento
        navegador.execute_script('document.querySelector("#divArvoreAcoes > a:nth-child(1) > img").click()')

        print("Documento incluído!")

        # clicar em Ofício
        sleep(1)  # Aumentado para headless
        navegador.execute_script("document.querySelectorAll('a').forEach(a => a.textContent.trim() === 'Ofício' && a.click());")

        print("Tipo Ofício selecionado!")

        sleep(2)  # Aumentado para headless
        # clicar em Público
        navegador.execute_script('document.querySelector("#optPublico").click()')
        sleep(1)  # Aumentado para headless

        # clicar em Salvar
        navegador.execute_script('document.querySelector("#btnSalvar").click()')
        
        print("Ofício salvo!")
        
        sleep(12)  # Aumentado para headless - aguardar nova janela abrir

        # mudar a janela - esperar até ter 2 janelas
        wait = WebDriverWait(navegador, 20)
        wait.until(lambda d: len(d.window_handles) > 1)
        
        janela2 = navegador.window_handles[1]
        navegador.switch_to.window(janela2)
        
        sleep(2)  # Aguardar janela carregar completamente

        print("Inserindo conteúdo no editor...")

        # mudar o iframe - aguardar estar presente
        iframe = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#cke_4_contents > iframe")))
        navegador.switch_to.frame(iframe)
        
        sleep(1)  # Aguardar iframe carregar
        
        navegador.execute_script(f"document.body.innerHTML = `{123456}`")
        
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
        
        print("Documento salvo! Iniciando marcação...")
        
        # ============= INÍCIO DA MARCAÇÃO (marcador.py) =============
        
        # Voltar para a janela principal
        navegador.switch_to.window(navegador.window_handles[0])
        navegador.switch_to.default_content()
        
        sleep(1)  # Aguardar foco na janela
        
        print("Pesquisando processo para marcação...")
        
        # Pesquisar o processo novamente
        campo_pesquisa = wait.until(EC.presence_of_element_located((By.ID, "txtPesquisaRapida")))
        campo_pesquisa.clear()
        sleep(0.5)
        campo_pesquisa.send_keys(123456)
        campo_pesquisa.send_keys(Keys.ENTER)
        
        sleep(2)  # Aumentado para headless
        
        # Mudar para o frame de visualização
        wait = WebDriverWait(navegador, 15)  # Aumentado timeout
        frame_2 = wait.until(EC.presence_of_element_located((By.ID, 'ifrVisualizacao')))
        navegador.switch_to.frame(frame_2)
        
        sleep(2)  # Aguardar frame carregar
        
        print("Adicionando anotação...")
        
        sleep(3)  # Aumentado para headless - Aguardar carregamento da página
        
        # Clicar em adicionar anotação - tentar diferentes métodos
        try:
            # Método 1: Procurar link com texto contendo "marcador_gerenciar"
            links = navegador.find_elements(By.CSS_SELECTOR, '#divArvoreAcoes a')
            link_encontrado = False
            for link in links:
                href = link.get_attribute('href') or ''
                if 'marcador_gerenciar' in href:
                    navegador.execute_script("arguments[0].click();", link)
                    link_encontrado = True
                    break
            
            if not link_encontrado:
                raise Exception("Link marcador_gerenciar não encontrado")
        except:
            try:
                # Método 2: Aguardar e clicar via JavaScript
                wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="divArvoreAcoes"]/a[24]')))
                navegador.execute_script('document.querySelector("#divArvoreAcoes > a:nth-child(24)").click()')
            except:
                # Método 3: Clicar diretamente no elemento
                try:
                    btn_anotacao = navegador.find_element(By.XPATH, '//*[@id="divArvoreAcoes"]/a[24]')
                    navegador.execute_script("arguments[0].click();", btn_anotacao)
                except:
                    # Método 4: Link pelo texto/título
                    links = navegador.find_elements(By.CSS_SELECTOR, '#divArvoreAcoes a')
                    for link in links:
                        if 'Anotação' in link.get_attribute('title') or 'Anotar' in link.get_attribute('title'):
                            navegador.execute_script("arguments[0].click();", link)
                            break
                    
        sleep(1)  # Aumentado para headless
        if True:
            
            navegador.execute_script('document.querySelector("#btnAdicionar").click()')
        
        sleep(2)  # Aumentado para headless
        
        # Clicar no seletor de marcador
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#selMarcador > div > span')))
            sleep(1)  # Aguardar antes de clicar
            navegador.execute_script('document.querySelector("#selMarcador > div > span").click()')
        except:
            # Tentar método alternativo
            navegador.find_element(By.CSS_SELECTOR, '#selMarcador').click()
        
        sleep(2)  # Aumentado para headless
        
        sleep(2)  # Aumentado para headless
        
        # Aguardar que as opções estejam visíveis
        opcoes = WebDriverWait(navegador, 15).until(  # Aumentado timeout
            EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "a.dd-option"))
        )
        
        sleep(1)  # Aumentado para headless
        
        # Iterar sobre as opções e clicar na etiqueta correta
        etiqueta_encontrada = False
        for opcao in opcoes:
            texto = opcao.text.strip()
            if texto == "teste":
                sleep(0.5)  # Pequeno delay antes de clicar
                navegador.execute_script("arguments[0].click();", opcao)
                etiqueta_encontrada = True
                break
        
        if not etiqueta_encontrada:
            print(f"⚠️ Etiqueta 'teste' não encontrada, usando primeira opção")
            navegador.execute_script("arguments[0].click();", opcoes[0])
        
        sleep(1)  # Aumentado para headless
        
        # Inserir a mensagem
        textarea = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="txaTexto"]')))
        sleep(0.5)
        textarea.clear()
        textarea.send_keys("teste")
        
        sleep(1)  # Aumentado para headless
        
        # Salvar anotação
        btn_salvar = navegador.find_element(By.XPATH, '//*[@id="sbmSalvar"]')
        navegador.execute_script("arguments[0].click();", btn_salvar)
        
        sleep(3)  # Aumentado para headless - Aguardar salvamento
        
        print("Anotação adicionada! Atribuindo processo...")
        
        # Atualizar a página
        navegador.refresh()
        sleep(3)  # Aumentado para headless
        
        # Mudar para o frame correto
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, 'ifrVisualizacao')))
        
        sleep(2)  # Aumentado para headless
        
        # Clicar em atribuir processo
        try:
            btn_atribuir = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="divArvoreAcoes"]/a[8]')))
            sleep(0.5)
            navegador.execute_script("arguments[0].click();", btn_atribuir)
        except:
            # Tentar encontrar pelo título
            links = navegador.find_elements(By.CSS_SELECTOR, '#divArvoreAcoes a')
            for link in links:
                titulo = link.get_attribute('title')
                if titulo and 'Atribuir' in titulo:
                    navegador.execute_script("arguments[0].click();", link)
                    break
        
        sleep(2)  # Aumentado para headless
        
        # Converter atribuição para o formato correto
        atribuicao_formatada = "teste"
        
        print(f"Atribuindo para: {atribuicao_formatada}")
        
        # Aguardar o select estar presente
        wait.until(EC.presence_of_element_located((By.ID, "selAtribuicao")))
        sleep(1)  # Aguardar select carregar completamente
        
        # Script JavaScript para selecionar a atribuição
        script = f"""
        var atribuicao = "{atribuicao_formatada}";
        var selectElement = document.querySelector("#selAtribuicao");
        if (selectElement) {{
            for (var i = 0; i < selectElement.options.length; i++) {{
                if (selectElement.options[i].text === atribuicao) {{
                    selectElement.selectedIndex = i;
                    selectElement.dispatchEvent(new Event('change'));
                    return true;
                }}
            }}
        }}
        return false;
        """
        resultado = navegador.execute_script(script)
        
        if not resultado:
            print(f"⚠️ Atribuição '{atribuicao_formatada}' não encontrada")
        
        sleep(1)  # Aumentado para headless
        
        # Salvar atribuição
        btn_salvar_atrib = navegador.find_element(By.XPATH, '//*[@id="sbmSalvar"]')
        navegador.execute_script("arguments[0].click();", btn_salvar_atrib)
        
        sleep(3)  # Aumentado para headless
        
        print("✅ SUCESSO COMPLETO! Ofício criado, marcado e atribuído!")
        
        # ============= FIM DA MARCAÇÃO =============
        
        
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
