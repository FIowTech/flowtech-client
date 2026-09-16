import platform
import subprocess
import socket
import mysql.connector

import psutil
from datetime import datetime
import time

from pathlib import Path

conexao = mysql.connector.connect(
    host="localhost",
    user="aluno",
    password="sptech",
    database="flowtech"
)

cursor = conexao.cursor(dictionary=True)

def obter_uuid_da_placa():
    sistema = platform.system().lower()

    if sistema == "windows":
        cmd = ["powershell", "-Command", "(Get-CimInstance -ClassName Win32_ComputerSystemProduct).UUID"]
        return subprocess.check_output(cmd, text=True, creationflags=subprocess.CREATE_NO_WINDOW).strip()
    
    elif sistema == "linux":
        return subprocess.check_output("sudo cat /sys/class/dmi/id/product_uuid", shell=True, text=True).strip()
    
    elif sistema == "darwin":
        cmd = "ioreg -rd1 -c IOPlatformExpertDevice | awk -F'\"' '/IOPlatformUUID/ {print $4}'"
        return subprocess.check_output(cmd, shell=True, text=True).strip()

    else:
        return None
    
def coletar_dados(usuario, maquina, uuid, id_embarcado):
    print("Programa Iniciado.")
    
    comando_sql = "SELECT * FROM parametros p INNER JOIN componentes c ON p.fk_componente = c.id WHERE p.fk_embarcado = %s;"

    cursor.execute(comando_sql, (id_embarcado, ))
    resultados = cursor.fetchall()
    
    alvo_cpu = None
    alvo_ram = None
    alvo_disco = None
    alvo_rede = None
    
    if not resultados:
        print("Não foram definidos parâmetros especificos... buscando o padrão.")
        alvo_cpu = alvo_ram = alvo_disco = alvo_rede = True
        
    
    for item in resultados:
        if item["nome"] == "cpu":
            alvo_cpu = True
        if item["nome"] == "ram":
            alvo_ram = True
        if item["nome"] == "disco":
            alvo_disco = True
        if item["nome"] == "rede":
            alvo_rede = True

    cursor.close()
    conexao.close()
    del resultados

    print(f"Olá {usuario}, aqui estão os dados da sua máquina (aguarde 15 seg):")

    data_atual = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"./{maquina}_{uuid}_{data_atual}.csv"

    if not Path(f"./{nome_arquivo}").exists():
        with open(f'./{nome_arquivo}', 'a', newline='') as csvfile:
            csvfile.write("maquina,uuid,cpu,disco,memoria,rede,data/hora\n")

    for i in range(25):
        cpu = psutil.cpu_percent(interval=1) if alvo_cpu else None
        ram = psutil.virtual_memory().percent if alvo_ram else None
        disco = psutil.disk_usage("/").percent if alvo_disco else None
        if alvo_rede == True:
            rede_inicio = psutil.net_io_counters() 
            time.sleep(10)
            rede_fim = psutil.net_io_counters()
            upload_mbps = f"{(rede_fim.bytes_sent - rede_inicio.bytes_sent) * 8 / 1_000_000:.3f}"
        else:
            upload_mbps = None
            
        data_hora = datetime.now().replace(microsecond=0)

        with open(f'./{nome_arquivo}', 'a', newline='') as csvfile:
            csvfile.write(f"{maquina},{uuid},{cpu},{ram},{disco},{upload_mbps},{data_hora}\n")

        time.sleep(4)

        if alvo_cpu: print(f"CPU: {cpu}%")
        if alvo_ram: print(f"Memória: {ram}%")
        if alvo_disco: print(f"Disco: {disco}%")
        if alvo_rede: print(f"Rede: {upload_mbps} Mbps")
        print("Data e hora local:", data_hora)
        print("---------------------------------------------")

    print("Programa encerrado.")
    
def login():
    email = input("Email: ")
    passwd = input("Senha: ")
    
    comando_sql = "SELECT u.id as id_usuario, u.email, u.senha, u.username, e.id as id_empresa, e.nome_fantasia FROM usuarios u INNER JOIN empresas e ON u.fk_empresa = e.id WHERE u.email = %s AND u.senha = %s;"
    dados_usuario = (email, passwd)

    cursor.execute(comando_sql, dados_usuario)
    resultados = cursor.fetchone()

    if not resultados:
        print("Operação invalida: Usuário não encontrado! Acesse www.freeflow.com e realize seu cadastro.")
        return

    usuario = resultados["username"]

    print("Login realizado com sucesso!")
    print(f"Seja bem-vindo {usuario}")
    id_empresa_usuario = resultados["id_empresa"]
    del resultados
    del comando_sql
    del dados_usuario
    
    comando_sql = "SELECT emp.id as id_empresa, p.id as id_porticos, emb.id as id_embarcado, emb.uuid, emb.status FROM empresas as emp INNER JOIN porticos as p ON emp.id = p.fk_empresa INNER JOIN embarcados as emb ON p.id = emb.fk_portico WHERE emb.uuid = %s;"
    uuid = obter_uuid_da_placa()
    cursor.execute(comando_sql, (uuid, ))
    resultados = cursor.fetchone()
    
    if not resultados:
        print("Operação inválida: Máquina não está cadastrada, por favor insira em sua dashboard")
        return
    
    id_empresa_embarcado = resultados["id_empresa"]
    
    if id_empresa_embarcado != id_empresa_usuario:
        print("Operação inválida: Esse embarcado não pertence a sua empresa")
        return
    
    status = resultados["status"]
    
    if status == 0:
        print("Operação inválida: Máquina desativada, altere seu status na dashboard")
        return
    
    id_embarcado = resultados["id_embarcado"]
    del resultados
    del comando_sql
    print("Sucesso: Iniciando a coleta de dados...")
    hostname = socket.gethostname()
    coletar_dados(usuario, hostname, uuid, id_embarcado)
    
login()