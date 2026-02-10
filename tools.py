import os
import socket
import re
import logging
import subprocess
import random
import time
from dotenv import load_dotenv
import pexpect
from time import sleep

# lib para PDF
from pdf_generator import *

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()  # Carrega variáveis de ambiente

# Variáveis Globais / Configuração
USUARIO = os.getenv('MYNUMBER')
SENHA = os.getenv('MYPASS')
CAMINHO_PW3270 = os.getenv('CAMINHO_ARQ')
SISTEMA = os.getenv('SYSTEM')
SECRET_CODE = os.getenv('SECRETCODE')
EMAIL_ADMIN = os.getenv('EMAIL_USER_ADMIN')

# Configuração de intervalo (padrão 100ms se não definido)
try:
    INTERVALO_TECLAS_MS = int(os.getenv('ITV_TECLAS', '50'))
except ValueError:
    INTERVALO_TECLAS_MS = 50
INTERVALO_TECLAS_SEC = INTERVALO_TECLAS_MS / 1000.0


def liberar_porta(porta):
    """Mata processos que estejam ocupando a porta especificada."""
    try:
        # Verifica se há algum processo usando a porta
        result = subprocess.run(
            ["lsof", "-t", f"-i:{porta}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode == 0 and result.stdout:
            pids = result.stdout.strip().split("\n")
            for pid in pids:
                if pid.strip().isdigit():
                    subprocess.run(["kill", "-9", pid.strip()])
                    logging.info(f"✔ Processo {pid} finalizado na porta {porta}")
    except FileNotFoundError:
        logging.warning("Comando 'lsof' não encontrado. Pule esta etapa se não estiver no Linux.")
    except Exception as e:
        logging.error(f"Erro ao liberar porta {porta}: {e}")

def iniciar_c3270(host='192.168.2.1', porta=5000):
    liberar_porta(porta)  # 🔪 Libera a porta antes de iniciar
    
    # Inicia o c3270 com scriptport ativado
    # Adicionado try/except para capturar falhas no spawn
    try:
        child = pexpect.spawn(f'c3270 -scriptport {porta} {host}')
        time.sleep(1) # Aguarda inicialização
        return child
    except Exception as e:
        logging.error(f"Erro ao iniciar c3270: {e}")
        return None

def send_command(command, porta=5000):
    """Envia um comando para o c3270 via socket."""
    try:
        with socket.create_connection(('localhost', porta), timeout=30) as sock:
            sock.sendall((command + '\n').encode())
            result = b""
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                result += data
                # O c3270 retorna "data: ..." e termina com "ok" ou "error"
                if b'ok' in data or b'error' in data:
                    break
            return result.decode(errors="ignore")
    except ConnectionRefusedError:
        logging.error(f"Não foi possível conectar na porta {porta}. O c3270 está rodando?")
        return ""
    except Exception as e:
        logging.error(f"Erro no send_command: {e}")
        return ""

def wait_unlock(porta=5000):
    """Aguarda o desbloqueio do terminal (X System)."""
    send_command("Wait(Unlock)", porta)

def get_tela_atual():
    """Captura e formata a tela atual do terminal."""
    raw = send_command('Ascii()')
    linhas = []

    for line in raw.splitlines():
        if line.startswith("data: "):
            # Remove o prefixo "data: " e mantém o conteúdo da linha
            linhas.append(line[6:].rstrip())
        elif line == "data:":
            # Linha vazia retornada pelo c3270
            linhas.append("")

    return '\n'.join(linhas).strip()

def escrever(texto):
    """Envia uma string para ser digitada."""
    wait_unlock()
    # Aspas precisam ser escapadas se estiverem no texto, 
    # mas para simplicidade aqui assumimos texto simples ou tratamos depois
    send_command(f'String("{texto}")')

def tecla(tecla_nome):
    """Envia uma tecla de função (Enter, Tab, PF1, etc)."""
    wait_unlock()
    send_command(tecla_nome)

def fechar_c3270(child):
    """Fecha o c3270 matando o processo diretamente."""
    if child:
        try:
            child.terminate(force=True)
            child.wait()
        except Exception:
            pass
        finally:
            try:
                child.close()
            except Exception:
                pass

def update_env_variable(key, value, env_file=".env"):
    """Atualiza ou adiciona uma variável no arquivo .env"""
    lines = []
    key_found = False

    if os.path.exists(env_file):
        with open(env_file, "r") as file:
            for line in file:
                if line.startswith(f"{key}="):
                    lines.append(f"{key}={value}\n")
                    key_found = True
                else:
                    lines.append(line)

    if not key_found:
        lines.append(f"{key}={value}\n")

    with open(env_file, "w") as file:
        file.writelines(lines)

    load_dotenv(override=True)

def gerar_nova_senha():
    consoantes = list("bcdfghjklmnpqrstvwxyz")
    numeros = list("123456789")
    password = "".join(random.choices(consoantes, k=4)) + "".join(random.choices(numeros, k=4))
    return password

def digitar_dados(usuario_login, senha_login, sistema_login):
    """Realiza o processo de login."""
    time.sleep(1)  # Garantir que o foco esteja na aplicação

    if not sistema_login or not usuario_login or not senha_login:
        logging.error("Credenciais ou sistema não definidos.")
        # Tenta continuar mesmo assim ou retorna? O original tentava.
        # return 

    # Sistema a ser acessado
    escrever("CBMMG")
    time.sleep(INTERVALO_TECLAS_SEC)
    tecla("tab")
    time.sleep(INTERVALO_TECLAS_SEC)

    # Insere o usuario
    escrever(usuario_login)
    time.sleep(INTERVALO_TECLAS_SEC)
    tecla("tab")
    time.sleep(INTERVALO_TECLAS_SEC)
    
    # Insere a senha
    escrever(senha_login)
    time.sleep(INTERVALO_TECLAS_SEC)
    tecla("enter")
    time.sleep(1)  # Aguarda processamento do login

    # Loop de verificação
    for _ in range(5): # Evita loop infinito, tenta 5 vezes
        mensagem1 = get_tela_atual()

        if "Senha expirada" in mensagem1:
            logging.warning("Senha expirada... favor gerar nova senha")
            return # Ou tratar a troca de senha aqui

        elif "Logon executado com sucesso" in mensagem1:
            logging.info("'Logon executado com sucesso' encontrado.")
            escrever(sistema_login)
            time.sleep(INTERVALO_TECLAS_SEC)
            tecla("enter")
            return
        else:
            # Se não achou nada, pode ser uma tela intermediária, manda enter
            tecla("enter")
            time.sleep(INTERVALO_TECLAS_SEC)
    
    logging.warning("Não foi possível confirmar o login após várias tentativas.")

def consultar_ns(ns_bm):
    """Consulta IP, DB e FU para um único NS/BM. Abre c3270, faz login, consulta e fecha."""
    # 1. Abre o emulador
    terminal = iniciar_c3270()
    if not terminal:
        logging.error("Falha ao iniciar emulador.")
        return None

    time.sleep(1)

    # 2. Login
    digitar_dados(USUARIO, SENHA, SISTEMA)

    logging.info(f"Iniciando processo para NS/BM: {ns_bm}")

    dicio_tela = {}

    # Pegar Tela de IP
    escrever("P")
    time.sleep(INTERVALO_TECLAS_SEC)
    escrever("IP")
    time.sleep(INTERVALO_TECLAS_SEC)
    escrever("SM")
    time.sleep(INTERVALO_TECLAS_SEC)
    tecla("enter")
    time.sleep(INTERVALO_TECLAS_SEC)
    escrever(ns_bm)
    time.sleep(INTERVALO_TECLAS_SEC)
    tecla("enter")
    time.sleep(INTERVALO_TECLAS_SEC)

    # Verifica se o NS/BM é válido
    tela_validacao = get_tela_atual()
    if "DIGITO VERIFICADOR INCORRETO" in tela_validacao:
        logging.error(f"NS/BM {ns_bm} inválido: DIGITO VERIFICADOR INCORRETO")
        fechar_c3270(terminal)
        return None

    escrever("X")
    time.sleep(INTERVALO_TECLAS_SEC)
    tecla("enter")
    time.sleep(INTERVALO_TECLAS_SEC)

    dicio_tela["Tela IP"] = get_tela_atual()

    for _ in range(2):
        tecla("tab")
        time.sleep(INTERVALO_TECLAS_SEC)

    # Pegar Tela de DB
    escrever("P")
    time.sleep(INTERVALO_TECLAS_SEC)
    escrever("DB")
    time.sleep(INTERVALO_TECLAS_SEC)
    tecla("enter")
    time.sleep(INTERVALO_TECLAS_SEC)

    dicio_tela["Tela DB"] = get_tela_atual()

    # Pegar Tela de FU
    for _ in range(3):
        tecla("tab")
        time.sleep(INTERVALO_TECLAS_SEC)

    escrever("P")
    time.sleep(INTERVALO_TECLAS_SEC)
    escrever("FU")
    time.sleep(INTERVALO_TECLAS_SEC)
    tecla("enter")
    time.sleep(INTERVALO_TECLAS_SEC)

    dicio_tela["Tela FU"] = get_tela_atual()

    # Segunda Tela de FU
    tecla("enter")
    time.sleep(INTERVALO_TECLAS_SEC)
    escrever("X")
    time.sleep(INTERVALO_TECLAS_SEC)
    tecla("enter")
    time.sleep(INTERVALO_TECLAS_SEC)

    dicio_tela["Tela FU 2"] = get_tela_atual()

    # Gerar PDF
    generate_pdf_from_screens(dicio_tela, output_dir="./saida_extratos", nsbm_override=ns_bm)
    logging.info(f"Processo para NS/BM {ns_bm} concluído. PDF gerado.")

    # Fecha o c3270 completamente
    fechar_c3270(terminal)
    time.sleep(1)

    return True


def initialize_main(lista_ns):
    for ns in lista_ns:
        resultado = consultar_ns(ns)
        if not resultado:
            logging.error(f"Falha ao processar NS/BM: {ns}")
        time.sleep(1)  # Pausa entre sessões
    
    # Ao final de todos, mescla os PDFs
    logging.info("Unificando PDFs gerados...")
    merge_pdfs_in_folder("./saida_extratos", "Anexo EXTRATO DB FU IP.pdf")

if __name__ == "__main__":
    ns_bm = ["1429240", "1363621"]
    
    initialize_main(ns_bm)    
    sleep(2)