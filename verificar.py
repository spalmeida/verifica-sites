#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de automação para verificação de sites WordPress com diversas funcionalidades,
utilizando a biblioteca Rich para exibir resultados de forma elegante e profissional.
O script cria um ambiente virtual (se necessário) e instala as dependências 
(requests, beautifulsoup4, rich, selenium, webdriver-manager).

Funcionalidades:
  - Cria ambiente virtual automaticamente (pasta "venv") e instala dependências se necessário.
  - Garante que o screenshot da página inicial seja capturado usando Selenium (em modo headless).
  - Exibe uma barra de progresso geral baseada no número total de verificações (16 passos por site),
    atualizando a descrição para indicar qual site e qual passo está sendo executado.
  - Realiza diversas verificações:
      1. Verificar disponibilidade do site (usando 5 métodos);
      2. Medir tempo de resposta;
      3. Verificar redirecionamentos;
      4. Verificar certificado SSL (se HTTPS);
      5. Verificar DNS;
      6. Executar teste de ping;
      7. Obter Content-Type;
      8. Extrair título da página;
      9. Verificar padrões de erro no conteúdo;
      10. Verificar existência de robots.txt;
      11. Verificar existência de sitemap.xml;
      12. Verificar meta refresh;
      13. Executar verificações específicas para WordPress;
      14. Salvar conteúdo (controle de versões);
      15. Medir desempenho geral da página inicial (baseado no tempo de resposta);
      16. Capturar screenshot da página inicial (primeira dobra) e salvar na pasta "print" (sobrescrevendo sempre).
  - Calcula uma nota (score) de 0 a 100% com base nos resultados (exceto o print) e exibe essa avaliação com cores:
      * 0 a 40%: vermelho;
      * 41 a 90%: amarelo;
      * 91 a 100%: verde claro.
  - Exibe os resultados de cada site utilizando painéis e tabelas do Rich, incluindo um item "Print" com um link clicável para o screenshot.
"""

import sys
import os
import subprocess

# ==================== Parte 1: Ambiente Virtual e Instalação de Dependências ====================
def in_virtualenv():
    return sys.prefix != getattr(sys, "base_prefix", sys.prefix)

if not in_virtualenv():
    venv_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv")
    if not os.path.exists(venv_dir):
        print("Ambiente virtual não detectado. Criando o ambiente virtual em 'venv'...")
        subprocess.check_call([sys.executable, "-m", "venv", "venv"])
    if os.name == "nt":
        python_executable = os.path.join(venv_dir, "Scripts", "python.exe")
    else:
        python_executable = os.path.join(venv_dir, "bin", "python")
    subprocess.check_call([python_executable, "-m", "pip", "install", "--upgrade", "pip"])
    # Instala as dependências necessárias, agora incluindo selenium e webdriver-manager
    subprocess.check_call([python_executable, "-m", "pip", "install", "requests", "beautifulsoup4", "rich", "selenium", "webdriver-manager"])
    subprocess.check_call([python_executable] + sys.argv)
    sys.exit()

# ==================== Parte 2: Importações e Configurações ====================
import time
import socket
import ssl
import hashlib
import datetime
from urllib.parse import urlparse
import asyncio

import requests
from bs4 import BeautifulSoup
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn

# Importa Selenium e WebDriver Manager para capturar o screenshot
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

console = Console()

LINKS_FILE = "links.txt"
BASE_DOWNLOAD_FOLDER = "dominios"

# ==================== Funções Auxiliares de Armazenamento ====================
def criar_pastas_necessarias(dominio):
    if not os.path.exists(BASE_DOWNLOAD_FOLDER):
        os.makedirs(BASE_DOWNLOAD_FOLDER)
    dominio_path = os.path.join(BASE_DOWNLOAD_FOLDER, dominio)
    if not os.path.exists(dominio_path):
        os.makedirs(dominio_path)
    return dominio_path

def calcular_hash(conteudo):
    md5 = hashlib.md5()
    md5.update(conteudo)
    return md5.hexdigest()

def contar_versoes(dominio_path, data_base):
    contador = 0
    for arquivo in os.listdir(dominio_path):
        if arquivo.startswith(data_base) and arquivo.endswith(".html"):
            contador += 1
    return contador

def get_last_version_file(dominio_path, data_base):
    versoes = []
    for arquivo in os.listdir(dominio_path):
        if arquivo.startswith(data_base) and arquivo.endswith(".html"):
            if arquivo == f"{data_base}.html":
                versoes.append((0, arquivo))
            else:
                try:
                    sufixo = arquivo.replace(data_base + "_", "").replace(".html", "")
                    versoes.append((int(sufixo), arquivo))
                except Exception:
                    continue
    if not versoes:
        return None
    versoes.sort(key=lambda x: x[0])
    return versoes[-1][1]

def salvar_conteudo(dominio_path, conteudo):
    """
    Salva o conteúdo baixado em um arquivo dentro da pasta do domínio.
    Se já existir um arquivo para o dia corrente, verifica:
      - Se o último arquivo foi salvo há menos de 10 minutos, NÃO cria nova versão.
      - Caso contrário, compara o hash do conteúdo atual com o último salvo.
        Se forem idênticos, não cria nova versão; se diferentes, cria nova versão com sufixo incremental.
    Retorna uma tupla (nome_do_arquivo_salvo ou None, número_total_de_versões).
    """
    hoje = datetime.datetime.now().strftime("%Y-%m-%d")
    now = time.time()
    threshold = 600  # 10 minutos
    ultimo_arquivo = get_last_version_file(dominio_path, hoje)
    if ultimo_arquivo:
        caminho_ultimo = os.path.join(dominio_path, ultimo_arquivo)
        mod_time = os.path.getmtime(caminho_ultimo)
        if now - mod_time < threshold:
            return None, contar_versoes(dominio_path, hoje)
        with open(caminho_ultimo, "rb") as f:
            conteudo_existente = f.read()
        if calcular_hash(conteudo_existente) == calcular_hash(conteudo):
            return None, contar_versoes(dominio_path, hoje)
        else:
            if ultimo_arquivo == f"{hoje}.html":
                novo_nome = f"{hoje}_1.html"
            else:
                try:
                    sufixo = ultimo_arquivo.replace(hoje + "_", "").replace(".html", "")
                    novo_nome = f"{hoje}_{int(sufixo) + 1}.html"
                except Exception:
                    novo_nome = f"{hoje}_1.html"
            caminho_arquivo = os.path.join(dominio_path, novo_nome)
    else:
        novo_nome = f"{hoje}.html"
        caminho_arquivo = os.path.join(dominio_path, novo_nome)
    with open(caminho_arquivo, "wb") as f:
        f.write(conteudo)
    return novo_nome, contar_versoes(dominio_path, hoje)

# ==================== Funções de Verificação Geral ====================
def verificar_site(url):
    resultados = []
    conteudo = None
    try:
        r1 = requests.get(url, timeout=10)
        resultados.append(r1.status_code == 200)
        if r1.status_code == 200 and conteudo is None:
            conteudo = r1.content
    except Exception:
        resultados.append(False)
    try:
        r2 = requests.head(url, timeout=10)
        resultados.append(r2.status_code < 400)
    except Exception:
        resultados.append(False)
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        r3 = requests.get(url, headers=headers, timeout=10)
        resultados.append(r3.status_code == 200)
        if r3.status_code == 200 and conteudo is None:
            conteudo = r3.content
    except Exception:
        resultados.append(False)
    try:
        url_barra = url if url.endswith("/") else url + "/"
        r4 = requests.get(url_barra, timeout=10)
        resultados.append(r4.status_code == 200)
        if r4.status_code == 200 and conteudo is None:
            conteudo = r4.content
    except Exception:
        resultados.append(False)
    try:
        parsed = urlparse(url)
        hostname = parsed.netloc if parsed.netloc else parsed.path
        sucesso_socket = False
        for port in [80, 443]:
            try:
                sock = socket.create_connection((hostname, port), timeout=10)
                sock.close()
                sucesso_socket = True
                break
            except Exception:
                continue
        resultados.append(sucesso_socket)
    except Exception:
        resultados.append(False)
    online = any(resultados)
    return online, conteudo

def extrair_dominio(url):
    parsed_url = urlparse(url)
    dominio = parsed_url.netloc
    if not dominio:
        dominio = parsed_url.path
    if dominio.startswith("www."):
        dominio = dominio[4:]
    return dominio

def ler_links(arquivo):
    if not os.path.exists(arquivo):
        console.print(f"[red]Arquivo de links '{arquivo}' não encontrado![/red]")
        sys.exit(1)
    links = []
    with open(arquivo, "r", encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if linha and not linha.startswith("#"):
                links.append(linha)
    return links

# ==================== Funções Adicionais de Verificação ====================
def check_response_time(url):
    try:
        start = time.time()
        r = requests.get(url, timeout=10)
        response_time = time.time() - start
        return response_time, r
    except Exception:
        return None, None

def check_redirection_chain(url):
    try:
        r = requests.get(url, allow_redirects=True, timeout=10)
        chain = [resp.url for resp in r.history]
        return chain
    except Exception:
        return []

def check_ssl_certificate(host, port=443):
    context = ssl.create_default_context()
    try:
        with socket.create_connection((host, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
                expiry = cert.get('notAfter')
                return True, expiry
    except Exception:
        return False, None

def check_dns_resolution(dominio):
    try:
        ip_list = socket.gethostbyname_ex(dominio)[2]
        return ip_list
    except Exception:
        return []

def ping_host(dominio):
    try:
        param = '-n' if os.name == 'nt' else '-c'
        command = ['ping', param, '1', dominio]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.returncode == 0
    except Exception:
        return False

def get_content_type(response):
    if response is not None:
        return response.headers.get('Content-Type', 'N/A')
    return 'N/A'

def get_page_title(content):
    try:
        soup = BeautifulSoup(content, 'html.parser')
        title = soup.title.string.strip() if soup.title and soup.title.string else 'N/A'
        return title
    except Exception:
        return 'N/A'

def check_error_patterns(content):
    error_keywords = ["404", "not found", "error", "503", "maintenance"]
    try:
        text = content.decode('utf-8', errors='ignore').lower()
    except Exception:
        text = ""
    errors_found = [word for word in error_keywords if word in text]
    return errors_found

def check_robots_txt(url):
    try:
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        r = requests.get(base + "/robots.txt", timeout=10)
        return r.status_code == 200
    except Exception:
        return False

def check_sitemap_xml(url):
    try:
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        r = requests.get(base + "/sitemap.xml", timeout=10)
        return r.status_code == 200
    except Exception:
        return False

def check_meta_refresh(content):
    try:
        soup = BeautifulSoup(content, 'html.parser')
        meta_refresh = soup.find('meta', attrs={'http-equiv': 'refresh'})
        return meta_refresh is not None
    except Exception:
        return False

# ==================== Funções Específicas para WordPress ====================
def check_wordpress_features(content, base_url):
    """
    Verifica características típicas de sites WordPress:
      - Presença de "wp-content" e "wp-includes" no HTML.
      - Meta tag "generator" indicando WordPress.
      - Disponibilidade dos endpoints "/wp-json/" e "/wp-admin/".
    Retorna um dicionário com os resultados.
    """
    features = {}
    text = ""
    try:
        text = content.decode('utf-8', errors='ignore').lower()
    except Exception:
        pass

    features["wp_content"] = "wp-content" in text
    features["wp_includes"] = "wp-includes" in text

    features["meta_generator"] = False
    try:
        soup = BeautifulSoup(content, "html.parser")
        meta = soup.find("meta", attrs={"name": "generator"})
        if meta and "wordpress" in meta.get("content", "").lower():
            features["meta_generator"] = True
    except Exception:
        pass

    try:
        wp_json_url = base_url.rstrip("/") + "/wp-json/"
        r = requests.get(wp_json_url, timeout=10)
        features["wp_json"] = (r.status_code == 200)
    except Exception:
        features["wp_json"] = False

    try:
        wp_admin_url = base_url.rstrip("/") + "/wp-admin/"
        r = requests.get(wp_admin_url, timeout=10)
        features["wp_admin"] = (r.status_code in [200, 302]) and ("login" in r.text.lower())
    except Exception:
        features["wp_admin"] = False

    return features

# ==================== Cálculo do Score ====================
def compute_score(online, resp_time, redir_chain, url, ssl_valid, dns_ips, ping_success,
                  content_type, title, error_patterns, robots, sitemap, meta_refresh):
    score = 0
    if online:
        score += 30
    if resp_time is not None:
        if resp_time < 1:
            score += 10
        elif resp_time < 3:
            score += 5
    if len(redir_chain) == 0:
        score += 10
    elif len(redir_chain) <= 2:
        score += 5
    if url.lower().startswith("https"):
        if ssl_valid:
            score += 10
    else:
        score += 5
    if dns_ips:
        score += 5
    if ping_success:
        score += 5
    if "text/html" in content_type.lower():
        score += 5
    if title != "N/A":
        score += 5
    if not error_patterns:
        score += 5
    if robots:
        score += 5
    if sitemap:
        score += 5
    if not meta_refresh:
        score += 5
    return score

# ==================== Novo Passo: Medir Desempenho da Página Inicial ====================
def medir_desempenho(resp_time):
    """
    Mede o desempenho da página inicial com base no tempo de resposta e retorna uma pontuação de 0 a 100%.
    Heurística utilizada:
      - Se resp_time < 0.5 s -> 100%
      - Se resp_time < 1 s -> 90%
      - Se resp_time < 1.5 s -> 80%
      - Se resp_time < 2 s -> 70%
      - Se resp_time < 2.5 s -> 60%
      - Caso contrário, 50%
    Se resp_time for None, retorna 0%.
    """
    if resp_time is None:
        return 0
    if resp_time < 0.5:
        return 100
    elif resp_time < 1:
        return 90
    elif resp_time < 1.5:
        return 80
    elif resp_time < 2:
        return 70
    elif resp_time < 2.5:
        return 60
    else:
        return 50

# ==================== Novo Passo: Capturar Screenshot da Página Inicial ====================
def take_screenshot(url, output_file):
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    import os
    import time

    # Silencia a saída do ChromeDriver
    os.environ["CHROME_DRIVER_SILENT_OUTPUT"] = "1"

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("window-size=1280,800")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument("--log-level=3")
    options.add_argument("--disable-logging")

    service = Service(ChromeDriverManager().install(), service_log_path=os.devnull)
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)
    time.sleep(2)  # Aguarda o carregamento da página
    driver.save_screenshot(output_file)
    driver.quit()

def print_ascii_art():
    art = r"""
### ###  ### ###  ### ##     ####   ### ###  ##  ##             ## ##     ####   #### ##  ### ###   ## ##
 ##  ##   ##  ##   ##  ##     ##     ##  ##  ##  ##            ##   ##     ##    # ## ##   ##  ##  ##   ##
 ##  ##   ##       ##  ##     ##     ##      ##  ##            ####        ##      ##      ##      ####
 ##  ##   ## ##    ## ##      ##     ## ##    ## ##             #####      ##      ##      ## ##    #####
 ### ##   ##       ## ##      ##     ##        ##                  ###     ##      ##      ##          ###
  ###     ##  ##   ##  ##     ##     ##        ##              ##   ##     ##      ##      ##  ##  ##   ##
   ##    ### ###  #### ##    ####   ####       ##               ## ##     ####    ####    ### ###   ## ##
"""
    console.print(art)

# ==================== Função Principal ====================
def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print_ascii_art()  # Exibe o ASCII art
    console.rule("[bold cyan]Iniciando verificação dos sites[/bold cyan]")
    links = ler_links(LINKS_FILE)
    total_links = len(links)
    if total_links == 0:
        console.print("[red]Nenhum link encontrado no arquivo.[/red]")
        sys.exit(1)
    
    # Barra de progresso geral: total_steps_overall = total_sites * 16 (16 passos por site)
    total_steps_overall = total_links * 16
    with Progress(
        SpinnerColumn(),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}% - {task.description}"),
        TimeElapsedColumn()
    ) as overall_progress:
        overall_task = overall_progress.add_task("Processando sites...", total=total_steps_overall)
        
        # Processa cada site individualmente
        for url in links:
            overall_progress.update(overall_task, description=f"Processando site: {url}")
            
            # Passo 1: Verificar disponibilidade do site
            online, conteudo = verificar_site(url)
            overall_progress.update(overall_task, advance=1, 
                description=f"{url} - Passo 1/16: Verificando disponibilidade")
            time.sleep(0.1)
            
            # Passo 2: Medir tempo de resposta
            resp_time, r_resp = check_response_time(url)
            overall_progress.update(overall_task, advance=1, 
                description=f"{url} - Passo 2/16: Medindo tempo de resposta")
            time.sleep(0.1)
            
            # Passo 3: Verificar redirecionamentos
            redir_chain = check_redirection_chain(url)
            overall_progress.update(overall_task, advance=1, 
                description=f"{url} - Passo 3/16: Verificando redirecionamentos")
            time.sleep(0.1)
            
            # Passo 4: Verificar certificado SSL (se HTTPS)
            if url.lower().startswith("https"):
                ssl_valid, ssl_expiry = check_ssl_certificate(extrair_dominio(url))
            else:
                ssl_valid = False
                ssl_expiry = None
            overall_progress.update(overall_task, advance=1, 
                description=f"{url} - Passo 4/16: Verificando certificado SSL")
            time.sleep(0.1)
            
            # Passo 5: Verificar DNS
            dns_ips = check_dns_resolution(extrair_dominio(url))
            overall_progress.update(overall_task, advance=1, 
                description=f"{url} - Passo 5/16: Verificando DNS")
            time.sleep(0.1)
            
            # Passo 6: Teste de ping
            ping_success = ping_host(extrair_dominio(url))
            overall_progress.update(overall_task, advance=1, 
                description=f"{url} - Passo 6/16: Executando teste de ping")
            time.sleep(0.1)
            
            # Passo 7: Obter Content-Type
            content_type = get_content_type(r_resp)
            overall_progress.update(overall_task, advance=1, 
                description=f"{url} - Passo 7/16: Obtendo Content-Type")
            time.sleep(0.1)
            
            # Passo 8: Obter título da página
            page_title = get_page_title(conteudo)
            overall_progress.update(overall_task, advance=1, 
                description=f"{url} - Passo 8/16: Extraindo título da página")
            time.sleep(0.1)
            
            # Passo 9: Verificar padrões de erro
            erros = check_error_patterns(conteudo)
            overall_progress.update(overall_task, advance=1, 
                description=f"{url} - Passo 9/16: Verificando padrões de erro")
            time.sleep(0.1)
            
            # Passo 10: Verificar robots.txt
            robots = check_robots_txt(url)
            overall_progress.update(overall_task, advance=1, 
                description=f"{url} - Passo 10/16: Verificando robots.txt")
            time.sleep(0.1)
            
            # Passo 11: Verificar sitemap.xml
            sitemap = check_sitemap_xml(url)
            overall_progress.update(overall_task, advance=1, 
                description=f"{url} - Passo 11/16: Verificando sitemap.xml")
            time.sleep(0.1)
            
            # Passo 12: Verificar meta refresh
            meta_refresh = check_meta_refresh(conteudo)
            overall_progress.update(overall_task, advance=1, 
                description=f"{url} - Passo 12/16: Verificando meta refresh")
            time.sleep(0.1)
            
            # Passo 13: Verificações específicas para WordPress
            base_url = url if url.startswith("http") else "http://" + url
            wp_features = check_wordpress_features(conteudo, base_url)
            overall_progress.update(overall_task, advance=1, 
                description=f"{url} - Passo 13/16: Verificando características WordPress")
            time.sleep(0.1)
            
            # Passo 14: Salvar conteúdo (controle de versões)
            dominio_site = extrair_dominio(url)
            dominio_path = criar_pastas_necessarias(dominio_site)
            novo_arquivo, total_versoes = salvar_conteudo(dominio_path, conteudo)
            nova_versao = "[green]Sim[/green]" if novo_arquivo is not None else "[grey]Não[/grey]"
            overall_progress.update(overall_task, advance=1, 
                description=f"{url} - Passo 14/16: Salvando conteúdo")
            time.sleep(0.1)
            
            # Passo 15: Medir desempenho geral da página inicial
            performance = medir_desempenho(resp_time)
            overall_progress.update(overall_task, advance=1, 
                description=f"{url} - Passo 15/16: Medindo desempenho")
            time.sleep(0.1)
            
            # Passo 16: Capturar screenshot da página inicial
            dominio_site = extrair_dominio(url)
            dominio_path = criar_pastas_necessarias(dominio_site)
            print_folder = os.path.join(dominio_path, "print")
            if not os.path.exists(print_folder):
                os.makedirs(print_folder)
            screenshot_file = os.path.join(print_folder, "homepage.png")
            try:
                take_screenshot(url, screenshot_file)
                screenshot_link = f"[link=file:///{screenshot_file.replace(os.sep, '/') }]{screenshot_file.replace(os.sep, '/') }[/link]"
                # Tenta abrir automaticamente o screenshot (opcional)
                import platform
                if platform.system() == "Windows":
                    os.startfile(screenshot_file)
                elif platform.system() == "Darwin":
                    subprocess.call(["open", screenshot_file])
                else:
                    subprocess.call(["xdg-open", screenshot_file])
            except Exception as e:
                screenshot_link = f"[red]Erro no print[/red]"
                console.print(f"[red]Erro ao capturar screenshot: {e}[/red]")
            time.sleep(0.1)
            
            # Aguarda um instante antes de prosseguir para o próximo site
            time.sleep(0.2)
            
            # Monta os dados para exibição dos resultados do site
            site_status = "[green]ONLINE[/green]" if online else "[red]OFFLINE[/red]"
            redir_str = f"[grey]{len(redir_chain)}[/grey]"
            if url.lower().startswith("https"):
                ssl_str = f"[green]Válido (expira: {ssl_expiry})[/green]" if ssl_valid else "[red]Inválido/N/A[/red]"
            else:
                ssl_str = "[grey]N/A[/grey]"
            dns_str = f"[grey]{', '.join(dns_ips)}[/grey]" if dns_ips else "[grey]N/A[/grey]"
            ping_str = "[green]Sucesso[/green]" if ping_success else "[red]Falha[/red]"
            resp_time_str = f"[grey]{resp_time:.2f} s[/grey]" if resp_time is not None else "[grey]N/A[/grey]"
            erros_str = f"[red]{', '.join(erros)}[/red]" if erros else "[green]Nenhum[/green]"
            
            # Tabela de verificações gerais
            table = Table(title=f"Detalhes da verificação para: [cyan]{url}[/cyan]", box=box.DOUBLE_EDGE)
            table.add_column("Item", style="bold", no_wrap=True)
            table.add_column("Resultado", style="dim")
            table.add_row("Status", site_status)
            table.add_row("Tempo de Resposta", resp_time_str)
            table.add_row("Redirecionamentos", redir_str)
            table.add_row("Certificado SSL", ssl_str)
            table.add_row("DNS", dns_str)
            table.add_row("Ping", ping_str)
            table.add_row("Content-Type", f"[grey]{content_type}[/grey]")
            table.add_row("Título", f"[grey]{page_title}[/grey]")
            table.add_row("Erros no Conteúdo", erros_str)
            table.add_row("robots.txt", "[green]Encontrado[/green]" if robots else "[orange]Não encontrado[/orange]")
            table.add_row("sitemap.xml", "[green]Encontrado[/green]" if sitemap else "[orange]Não encontrado[/orange]")
            table.add_row("Meta Refresh", "[red]Detectado[/red]" if meta_refresh else "[green]Não detectado[/green]")
            table.add_row("Nova Versão", nova_versao)
            table.add_row("Número de Versões", f"[orange]{total_versoes}[/orange]")
            table.add_row("Desempenho", f"[bold]{performance}%[/bold]")
            table.add_row("Print", screenshot_link)
            
            # Tabela de verificações específicas para WordPress
            wp_table = Table(title="Verificações WordPress", box=box.SIMPLE)
            wp_table.add_column("Item", style="bold", no_wrap=True)
            wp_table.add_column("Resultado", style="dim")
            wp_table.add_row("wp-content", "[green]Encontrado[/green]" if wp_features.get("wp_content") else "[red]Não encontrado[/red]")
            wp_table.add_row("wp-includes", "[green]Encontrado[/green]" if wp_features.get("wp_includes") else "[red]Não encontrado[/red]")
            wp_table.add_row("Meta Generator", "[green]WordPress detectado[/green]" if wp_features.get("meta_generator") else "[red]Não detectado[/red]")
            wp_table.add_row("WP-JSON", "[green]Acessível[/green]" if wp_features.get("wp_json") else "[red]Indisponível[/red]")
            wp_table.add_row("WP-Admin", "[green]Página de Login Detectada[/green]" if wp_features.get("wp_admin") else "[red]Não detectada[/red]")
            
            score = compute_score(online, resp_time, redir_chain, url, ssl_valid, dns_ips, ping_success,
                                  content_type, page_title, erros, robots, sitemap, meta_refresh)
            if score <= 40:
                score_style = "bold red"
            elif score <= 90:
                score_style = "bold yellow"
            else:
                score_style = "bold green"
            
            painel_conteudo = Panel.fit(
                table,
                title=f"Nota Final: [ {score} % ]",
                subtitle=f"[{score_style}]{score}%[/{score_style}]",
                border_style=score_style
            )
            painel_wp = Panel.fit(wp_table, title="WordPress", border_style="blue")
            
            console.print(painel_conteudo)
            console.print(painel_wp)
            console.rule()
            time.sleep(0.5)
    
    console.rule("[bold cyan]Processo finalizado[/bold cyan]")

if __name__ == "__main__":
    main()
