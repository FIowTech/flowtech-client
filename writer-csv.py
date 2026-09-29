import platform
import subprocess
import socket
import mysql.connector
from getmac import get_mac_address 
import speedtest

import psutil
from datetime import datetime
import time
from pathlib import Path


MAX_NUCLEOS = 16

conexao = mysql.connector.connect(
    host="localhost",
    user="aluno",
    password="Sptech#2024",
    database="flowtech"
)

cursor = conexao.cursor(dictionary=True)

mac_geral = get_mac_address().replace(":", "").upper()

def coletar_dados(usuario, mac_geral, id_embarcado):
    print("Programa Iniciado.")
    
    comando_sql = "SELECT * FROM parametro p INNER JOIN componente c ON p.componente_id = c.id_componente WHERE p.embarcado_id = %s;"

    cursor.execute(comando_sql, (id_embarcado, ))
    #resultados = cursor.fetchall()
    
    # alvo_cpu = None
    # alvo_ram = None
    # alvo_disco = None
    # alvo_rede = None
    
    # if not resultados:
    #     print("Não foram definidos parâmetros especificos... buscando o padrão.")
    #     alvo_cpu = alvo_ram = alvo_disco = alvo_rede = True
        
    
    # for item in resultados:
    #     if item["nome"] == "cpu":
    #         alvo_cpu = True
    #     if item["nome"] == "ram":
    #         alvo_ram = True
    #     if item["nome"] == "disco":
    #         alvo_disco = True
    #     if item["nome"] == "rede":
    #         alvo_rede = True



    # cursor.close()
    # conexao.close()
    # del resultados

    print(f"Olá {usuario}, aqui estão os dados da sua máquina (aguarde 15 seg):")

    data_atual = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"./{mac_geral}_{data_atual}.csv"

    if not Path(f"./{nome_arquivo}").exists():
        with open(f'./{nome_arquivo}', 'a', newline='') as csvfile:
            csvfile.write("mac, data/hora,cpu,qtd_cpu_fisica,qtd_cpu_logica,freq_cpu,ram_total,ram_usada,swap_total,swap_usada,disco_total,disco_usada,download,upload,latencia,cpu_1, cpu_2,cpu_3,cpu_4,cpu_5,cpu_6,cpu_7,cpu_8,cpu_9,cpu_10,cpu_11,cpu_12,cpu_13,cpu_14,cpu_15,cpu_16\n")
        
    for i in range(25):
        # CPU 
        cpu = psutil.cpu_percent(interval=1) # if alvo_cpu else None
        cpu_por_nucleo = psutil.cpu_percent(interval=None, percpu=True)
        qtd_cpu_fisica = psutil.cpu_count(logical=False)
        qtd_cpu_logica = psutil.cpu_count(logical=True)
        freq_cpu = psutil.cpu_freq()


        mensagem_nucleos = []
        for i in range(MAX_NUCLEOS):
             try:
                 mensagem_nucleos.append(cpu_por_nucleo[i])
             except IndexError:
                 mensagem_nucleos.append("")

        # RAM
        
        ramTotal = f"{psutil.virtual_memory().total / (1024 * 1024):.4f}"
        ramUsada = f"{psutil.virtual_memory().used / (1024 * 1024):.4f}" 
        swapTotal = psutil.swap_memory().total / (1024 * 1024)
        swapUsada = psutil.swap_memory().used / (1024 * 1024)


        # Disco
        discoTotal = psutil.disk_usage("/").total / (1024 * 1024) # if alvo_disco else None
        discoUsado = psutil.disk_usage("/").used / (1024 * 1024) # if alvo_disco else None
        
        # Rede
        rede_inicio = psutil.net_io_counters() 
        st = speedtest.Speedtest()
        latencia = st.results.ping
        
        time.sleep(4)
        rede_fim = psutil.net_io_counters()
        upload_mbps = f"{(rede_fim.bytes_sent - rede_inicio.bytes_sent) * 8 / 1_000_000:.3f}"
        download_mbps = f"{(rede_inicio.bytes_sent - rede_fim.bytes_sent) / 1000.0:.3f}"

         # Capturando processos
        #processos = list(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'status']))
        #total_processos = len(processos)

        data_hora = datetime.now().replace(microsecond=0)
        
        mensagem = []
        mensagem.append([mac_geral, data_hora,cpu,qtd_cpu_fisica,qtd_cpu_logica,freq_cpu,ramTotal, ramUsada,swapTotal,swapUsada,discoTotal,discoUsado,download_mbps,upload_mbps,latencia,*mensagem_nucleos])
        
        with open(f'./{nome_arquivo}', 'w', newline='') as csvfile:
            csvfile.write(f"{mensagem}")

        #time.sleep(4)

        #print(processos)
        print(f"CPU: {cpu}%")
        print(f"Memória: {ramUsada}%")
        print(f"Disco: {discoUsado}%")
        print(f"Rede Download: {download_mbps} Mbps")
        print(f"Rede Upload: {upload_mbps} Mbps")
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
    coletar_dados(usuario, mac_geral, id_embarcado)
    
login()