from playwright.sync_api import sync_playwright
from time import sleep
import os
from dotenv import load_dotenv

load_dotenv()

# Configurar proxy para ignorar localhost (resolver problema com proxy Prodemge)
os.environ['NO_PROXY'] = 'localhost,127.0.0.1'
os.environ['no_proxy'] = 'localhost,127.0.0.1'


def gerar_resposta(doc_sei):
    try:
        print("Iniciando processo...")

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-software-rasterizer',
                    '--disable-extensions',
                    '--disable-blink-features=AutomationControlled',
                    '--no-proxy-server',
                    "--proxy-server=direct://",
                    '--proxy-bypass-list=*',
                ],
            )

            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                ignore_https_errors=True,
            )
            page = context.new_page()

            user = os.getenv("USER_SEI")
            password = os.getenv("PASSWORD_SEI")
            orgao = os.getenv("ORGAO")

            print("Acessando o sistema SEI...")

            # acessa o site do SEI
            page.goto("https://www.sei.mg.gov.br/")

            # inserir o meu usuário
            page.fill("#txtUsuario", user)
            sleep(0.5)

            # inserir minha senha
            page.fill("#pwdSenha", password)

            # inserir o orgao
            page.select_option("#selOrgao", label=orgao)

            # clicar no botão acessar
            page.click("#Acessar")

            print("Login realizado com sucesso!")
            print("Varredura de documentos existentes...")

            # clicar em Pesquisar
            pesquisa = page.locator("#txtPesquisaRapida")
            pesquisa.fill(doc_sei)
            pesquisa.press("Enter")
            print('pesquisou')

            # mudar para o frame
            iframe = page.frame_locator("#ifrArvore")
            print('mudou para o frame ifrArvore')
            sleep(1)

            arvore_pross = iframe.locator("#divArvore")
            print('encontrou a arvore')

            elementos = arvore_pross.locator('div > a[target="ifrVisualizacao"] > span').all()

            print("Quantidade de elemento encontrados na árvore:", len(elementos))

            # lista com os textos visíveis
            docs_arvore = []
            for el in elementos:
                texto = el.text_content().strip()
                if not texto:
                    continue

                span_id = (el.get_attribute("id") or "").strip()
                if span_id.startswith("span"):
                    span_id = span_id.replace("span", "", 1)

                docs_arvore.append([span_id, texto])

            print(docs_arvore)

            sleep(100)  # Aguardar para visualização

            browser.close()
            return

    except Exception as e:
        print(f"❌ ERRO: {str(e)}", "error")


if __name__ == "__main__":
    # Documento Base do CEB
    documento_sei = "1400.01.0008514/2026-81"
    gerar_resposta(documento_sei)
