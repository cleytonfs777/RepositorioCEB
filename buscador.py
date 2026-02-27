async def construtor_off(request: OficioRequest):
    
    async def gerar_resposta():
        try:
            
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

            user = os.getenv("USER")
            password = os.getenv("PASSWORD")
            orgao = os.getenv("ORGAO")

            yield gerar_status("Acessando o sistema SEI...", "info", 5)
            
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

            yield gerar_status("Login realizado com sucesso!", "success", 15)
            yield gerar_status("Buscando conteúdo do ofício...", "info", 20)

            # buscar o conteudo do oficio
            pergunta_ia = busca_conteudo_oficio(request.doc_sei, navegador)
            
            yield gerar_status("Conteúdo encontrado! Gerando resposta com IA...", "info", 35)

            # passa o prompt para a ia
            resposta_ia = make_response(pergunta_ia, request.complementar)

            yield gerar_status("Resposta gerada pela IA!", "success", 50)
            yield gerar_status("Criando ofício...", "info", 55)

            # criar o oficio
            conteudo_oficio = cria_oficio(request.assunto, request.destinatario, request.signatario, request.graduacao, request.funcao, resposta_ia, request.ofreferencia)

            yield gerar_status("Mudando para frame padrão...", "info", 60)
            
            # voltar para o frame padrão
            navegador.switch_to.default_content()

            # clicar em Pesquisar
            pesquisa = navegador.find_element(By.ID, "txtPesquisaRapida")
            pesquisa.send_keys(request.processo)
            pesquisa.send_keys(Keys.ENTER)

            yield gerar_status(f"Processo {request.processo} encontrado!", "success", 65)

            sleep(1)
            # mudar o frame
            iframe = navegador.find_element(By.ID, "ifrVisualizacao")
            navegador.switch_to.frame(iframe)
            sleep(1)

            yield gerar_status("Incluindo documento...", "info", 70)

            # cliar em Incluir Documento
            navegador.execute_script('document.querySelector("#divArvoreAcoes > a:nth-child(1) > img").click()')

            yield gerar_status("Documento incluído!", "success", 75)

            # clicar em Ofício
            sleep(1)  # Aumentado para headless
            navegador.execute_script("document.querySelectorAll('a').forEach(a => a.textContent.trim() === 'Ofício' && a.click());")

            yield gerar_status("Tipo Ofício selecionado!", "info", 78)

            sleep(2)  # Aumentado para headless
            # clicar em Público
            navegador.execute_script('document.querySelector("#optPublico").click()')
            sleep(1)  # Aumentado para headless

            # clicar em Salvar
            navegador.execute_script('document.querySelector("#btnSalvar").click()')
            
            yield gerar_status("Ofício salvo!", "success", 82)
            
            sleep(12)  # Aumentado para headless - aguardar nova janela abrir

            # mudar a janela - esperar até ter 2 janelas
            wait = WebDriverWait(navegador, 20)
            wait.until(lambda d: len(d.window_handles) > 1)
            
            janela2 = navegador.window_handles[1]
            navegador.switch_to.window(janela2)
            
            sleep(2)  # Aguardar janela carregar completamente

            yield gerar_status("Inserindo conteúdo no editor...", "info", 85)

            # mudar o iframe - aguardar estar presente
            iframe = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#cke_4_contents > iframe")))
            navegador.switch_to.frame(iframe)
            
            sleep(1)  # Aguardar iframe carregar
            
            navegador.execute_script(f"document.body.innerHTML = `{conteudo_oficio}`")
            
            sleep(1)  # Aguardar conteúdo ser inserido
            
            yield gerar_status("Conteúdo inserido no ofício!", "success", 90)

            # salvar o documento
            navegador.switch_to.default_content()
            sleep(2)
            
            # Clicar no botão salvar com wait
            btn_salvar = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/div[1]/div[1]/div/div/span[2]/span[1]/span[3]/a")))
            navegador.execute_script("arguments[0].click();", btn_salvar)
            
            yield gerar_status("Salvando documento...", "info", 95)
            
            sleep(3)  # Aumentado para headless
            navegador.close()
            
            yield gerar_status("Documento salvo! Iniciando marcação...", "success", 96)
            
            # ============= INÍCIO DA MARCAÇÃO (marcador.py) =============
            
            # Voltar para a janela principal
            navegador.switch_to.window(navegador.window_handles[0])
            navegador.switch_to.default_content()
            
            sleep(1)  # Aguardar foco na janela
            
            yield gerar_status("Pesquisando processo para marcação...", "info", 97)
            
            # Pesquisar o processo novamente
            campo_pesquisa = wait.until(EC.presence_of_element_located((By.ID, "txtPesquisaRapida")))
            campo_pesquisa.clear()
            sleep(0.5)
            campo_pesquisa.send_keys(request.processo)
            campo_pesquisa.send_keys(Keys.ENTER)
            
            sleep(2)  # Aumentado para headless
            
            # Mudar para o frame de visualização
            wait = WebDriverWait(navegador, 15)  # Aumentado timeout
            frame_2 = wait.until(EC.presence_of_element_located((By.ID, 'ifrVisualizacao')))
            navegador.switch_to.frame(frame_2)
            
            sleep(2)  # Aguardar frame carregar
            
            yield gerar_status("Adicionando anotação...", "info", 98)
            
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
            if request.has_ticket:
                
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
                if texto == request.etiqueta:
                    sleep(0.5)  # Pequeno delay antes de clicar
                    navegador.execute_script("arguments[0].click();", opcao)
                    etiqueta_encontrada = True
                    break
            
            if not etiqueta_encontrada:
                yield gerar_status(f"⚠️ Etiqueta '{request.etiqueta}' não encontrada, usando primeira opção", "warning", 98)
                navegador.execute_script("arguments[0].click();", opcoes[0])
            
            sleep(1)  # Aumentado para headless
            
            # Inserir a mensagem
            textarea = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="txaTexto"]')))
            sleep(0.5)
            textarea.clear()
            textarea.send_keys(request.msg)
            
            sleep(1)  # Aumentado para headless
            
            # Salvar anotação
            btn_salvar = navegador.find_element(By.XPATH, '//*[@id="sbmSalvar"]')
            navegador.execute_script("arguments[0].click();", btn_salvar)
            
            sleep(3)  # Aumentado para headless - Aguardar salvamento
            
            yield gerar_status("Anotação adicionada! Atribuindo processo...", "success", 99)
            
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
            atribuicao_formatada = tranform_text_atribuicao(request.atribuicao)
            
            yield gerar_status(f"Atribuindo para: {atribuicao_formatada}", "info", 99)
            
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
                yield gerar_status(f"⚠️ Atribuição '{atribuicao_formatada}' não encontrada", "warning", 99)
            
            sleep(1)  # Aumentado para headless
            
            # Salvar atribuição
            btn_salvar_atrib = navegador.find_element(By.XPATH, '//*[@id="sbmSalvar"]')
            navegador.execute_script("arguments[0].click();", btn_salvar_atrib)
            
            sleep(3)  # Aumentado para headless
            
            yield gerar_status("✅ SUCESSO COMPLETO! Ofício criado, marcado e atribuído!", "success", 100)
            
            # ============= FIM DA MARCAÇÃO =============
            
            
        except Exception as e:
            yield gerar_status(f"❌ ERRO: {str(e)}", "error")
            try:
                navegador.quit()
            except:
                pass
    
    return StreamingResponse(gerar_resposta(), media_type="application/x-ndjson")
