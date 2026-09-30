import mysql.connector
from getmac import get_mac_address 
import speedtest
import csv
import psutil
from datetime import datetime, time
from pathlib import Path
import time
import os
from dotenv import load_dotenv
import getpass

load_dotenv()

conexao = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)

cursor = conexao.cursor(dictionary=True)

mac_geral = get_mac_address().replace(":", "").upper()
mac_geral_ponto = get_mac_address().upper()
MAX_NUCLEOS = 16

def coletar_dados(usuario, mac_geral, id_embarcado):
    print("Programa Iniciado.")
    
    comando_sql = "SELECT * FROM parametro p INNER JOIN componente c ON p.componente_id = c.id_componente WHERE p.embarcado_id = %s;"

    cursor.execute(comando_sql, (id_embarcado, ))

    print(f"Olá {usuario}, aqui estão os dados da sua máquina {mac_geral}(aguarde 15 seg):")

    data_atual = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"./{mac_geral}_{data_atual}.csv"

    if not Path(f"./{nome_arquivo}").exists():
        with open(f'./{nome_arquivo}', 'a', newline='') as csvfile:
            csvfile.write("endereco_mac,timestamp,cpu_uso_pct,qtd_cpu_fisica,qtd_cpu_logica,cpu_freq,cpu_freq_total,ram_uso_mb,ram_total_mb,swap_uso_mb,swap_total_mb,disco_uso_mb,disco_total_mb,maior_processo_cpu,maior_processo_ram,download_mbps,upload_mbps,latencia_ms,cpu_1,cpu_2,cpu_3,cpu_4,cpu_5,cpu_6,cpu_7,cpu_8,cpu_9,cpu_10,cpu_11,cpu_12,cpu_13,cpu_14,cpu_15,cpu_16\n")
        
    for i in range(25):
        cpu = psutil.cpu_percent() 
        cpu_por_nucleo = psutil.cpu_percent(percpu=True)
        qtd_cpu_fisica = psutil.cpu_count(logical=False)
        qtd_cpu_logica = psutil.cpu_count(logical=True)
        cpu_freq = f"{psutil.cpu_freq().current / 1000:.2f}"
        cpu_freq_total = f"{psutil.cpu_freq().max / 1000:.2f}"

        mensagem_nucleos = []
        for i in range(MAX_NUCLEOS):
             try:
                 mensagem_nucleos.append(cpu_por_nucleo[i])
             except IndexError:
                 mensagem_nucleos.append("")

        ramTotal = f"{psutil.virtual_memory().total / (1024 * 1024):.0f}"
        ramUsada = f"{psutil.virtual_memory().used / (1024 * 1024):.0f}" 
        swapTotal = f"{psutil.swap_memory().total / (1024 * 1024):.0f}"
        swapUsada = f"{psutil.swap_memory().used / (1024 * 1024):.0f}"

        discoTotal = f"{psutil.disk_usage("/").total / (1024 * 1024):.0f}"
        discoUsado = f"{psutil.disk_usage("/").used / (1024 * 1024):.0f}"

        st = speedtest.Speedtest()
        st.get_best_server()
        latencia = st.results.ping
        download_mbps = f"{st.download() / 1_000_000:.2f}"
        upload_mbps = f"{st.upload() / 1_000_000:.2f}"

        for processo in psutil.process_iter():
            try:
                processo.cpu_percent(None)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            
        time.sleep(1)

        maior_cpu = ""
        maior_percentual = 0

        for processo in psutil.process_iter(['pid', 'name']):
            try:
                uso_cpu = processo.cpu_percent(None)

                if uso_cpu > maior_percentual:
                    maior_percentual = uso_cpu
                    maior_cpu = processo

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        maior_ram = ""
        maior_memoria = 0

        for processo in psutil.process_iter(['pid', 'name', 'memory_info']):
            try:
                memoria = processo.info['memory_info'].rss 

                if memoria > maior_memoria:
                    maior_memoria = memoria
                    maior_ram = processo

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            
        timestamp = datetime.now().replace(microsecond=0).strftime('%Y-%m-%d %H:%M:%S')
        
        mensagem = [mac_geral,timestamp,cpu,qtd_cpu_fisica,qtd_cpu_logica,cpu_freq,cpu_freq_total,ramUsada,ramTotal,swapUsada,swapTotal,discoUsado,discoTotal,maior_cpu.name(),maior_ram.info['name'],download_mbps,upload_mbps,latencia,*mensagem_nucleos]

        with open(f'./{nome_arquivo}', 'a', newline='') as csvfile:
            arquivo = csv.writer(csvfile)
            arquivo.writerow(mensagem)

        print(f"CPU: {cpu}%")
        print(f"Memória: {ramUsada} (em GB's)")
        print(f"Disco: {discoUsado}%")
        print(f"Rede Download: {download_mbps} Mbps")
        print(f"Rede Upload: {upload_mbps} Mbps")
        print(f"Processo com maior uso de CPU: {maior_cpu.name()} | PID: {maior_cpu.pid}")
        print(f"Processo com maior uso de RAM: {maior_ram.info['name']} | PID: {maior_ram.info['pid']}")
        print("Data e hora local:", timestamp)
        print("---------------------------------------------")

    print("Programa encerrado.")
    
def login():
    email = input("Digite seu email: ")
    passwd = getpass.getpass("Digite sua senha: ", echo_char='*')
    
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
        cursor.execute(comando_sql, (mac_geral_ponto, ))
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