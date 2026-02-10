import pexpect
import time
import socket

# Inicia o c3270
print("Iniciando c3270...")
child = pexpect.spawn('c3270 -scriptport 5000 192.168.2.1', encoding='utf-8')
child.logfile_read = None  # Para capturar output

print("Aguardando 3 segundos...")
time.sleep(3)

print(f"c3270 está vivo? {child.isalive()}")
print(f"PID: {child.pid}")

# Tenta ler o que o c3270 retornou
try:
    index = child.expect([pexpect.TIMEOUT, pexpect.EOF], timeout=1)
    if index == 0:
        print("Timeout - processo ainda rodando")
        print(f"Buffer before: {child.before}")
    else:
        print("EOF - processo terminou")
except Exception as e:
    print(f"Erro ao ler: {e}")

# Tenta conectar no scriptport
print("\nTentando conectar na porta 5000...")
try:
    with socket.create_connection(('localhost', 5000), timeout=2) as sock:
        print("✓ Conectado!")
        sock.sendall(b'Query()\n')
        data = sock.recv(1024)
        print(f"Resposta: {data}")
except Exception as e:
    print(f"✗ Erro: {e}")

print("\nMatando o processo...")
child.terminate()
