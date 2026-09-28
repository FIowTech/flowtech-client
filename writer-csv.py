import platform
import subprocess
import socket
import mysql.connector
from getmac import get_mac_address 

import psutil
from datetime import datetime
import time

from pathlib import Path

conexao = mysql.connector.connect(
    host="localhost",
    user="aluno",
    password="Sptech#2024",
    database="flowtech"
)

cursor = conexao.cursor(dictionary=True)

mac_geral = get_mac_address().replace(":", "").upper()

    
def coletar_dados(usuario, maquina, mac_geral, id_embarcado):
    print("Programa Iniciado.")
    
    comando_sql = "SELECT * FROM parametro p INNER JOIN componente c ON p.componente_id = c.id_componente WHERE p.embarcado_id = %s;"

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
    nome_arquivo = f"./{maquina}_{mac_geral}_{data_atual}.csv"

    if not Path(f"./{nome_arquivo}").exists():
        with open(f'./{nome_arquivo}', 'a', newline='') as csvfile:
            csvfile.write("maquina,mac,cpu,disco,memoria,rede,data/hora\n")

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
            csvfile.write(f"{maquina},{mac_geral},{cpu},{ram},{disco},{upload_mbps},{data_hora}\n")

        time.sleep(4)

        if alvo_cpu: print(f"CPU: {cpu}%")
        if alvo_ram: print(f"Memória: {ram}%")
        if alvo_disco: print(f"Disco: {disco}%")
        if alvo_rede: print(f"Rede: {upload_mbps} Mbps")
        print("Data e hora local:", data_hora)
        print("---------------------------------------------")

    print("Programa encerrado.")
    
def login():
    email = "infra@flowtech.com.br"
    passwd = "Sptech#2026"
    
    comando_sql = "SELECT u.id_usuario, u.nome, u.email, u.senha, e.id_empresa, e.nome_fantasia FROM usuario u INNER JOIN empresa e ON u.empresa_id = e.id_empresa WHERE u.email = %s AND u.senha = sha2(%s,256);"
    dados_usuario = (email, passwd)

    cursor.execute(comando_sql, dados_usuario)
    resultados = cursor.fetchone()

    if not resultados:
        print("Operação invalida: Usuário não encontrado! Acesse www.freeflow.com e realize seu cadastro.")
        return

    usuario = resultados["nome"]

    print("Login realizado com sucesso!")
    print(f"Seja bem-vindo {usuario}")
    id_empresa_usuario = resultados["id_empresa"]
    del resultados
    del comando_sql
    del dados_usuario
    
    comando_sql = "SELECT emp.id_empresa, emb.id_embarcado, emb.endereco_mac, emb.status FROM empresa as emp INNER JOIN embarcado as emb ON emp.id_empresa = emb.empresa_id WHERE emb.endereco_mac = %s;"
    cursor.execute(comando_sql, (mac_geral, ))
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
    coletar_dados(usuario, hostname, mac_geral, id_embarcado)
    
login()


mensagem.append([id_maquina,hora, porcentagem_cpu,ram.total, ram.used, swap.total,swap.used,proc_rodando,proc_esperando,uso_disco.total, uso_disco.used,io_rede.bytes_sent,io_rede.bytes_recv,io_rede.dropin,io_rede.dropout,latencia])