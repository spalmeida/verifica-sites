  <header>
    <h1>Verificador de Sites WordPress</h1>
    <image src="https://github.com/user-attachments/assets/ea4e27b6-c29c-4f8c-9ffb-114e2718dabe" />
    <p>
      Este projeto é um script de automação em Python que realiza diversas verificações em sites WordPress e exibe os resultados de forma elegante no terminal utilizando a biblioteca <strong>Rich</strong>. O script cria (se necessário) um ambiente virtual, instala as dependências e executa várias análises, como verificação de disponibilidade, tempo de resposta, redirecionamentos, certificado SSL, DNS, teste de ping, extração de título, análise de erros, verificação de arquivos essenciais (<code>robots.txt</code>, <code>sitemap.xml</code>, <code>meta refresh</code>) e verificações específicas para WordPress. Além disso, o script captura um screenshot da página inicial usando <strong>Selenium</strong> e o <strong>WebDriver Manager</strong>.
    </p>
  </header>

  <section class="section">
    <h2>Funcionalidades</h2>
    <ul>
      <li><strong>Ambiente Virtual Automático:</strong> Cria automaticamente um ambiente virtual (pasta <code>venv</code>) e instala as dependências necessárias: <code>requests</code>, <code>beautifulsoup4</code>, <code>rich</code>, <code>selenium</code> e <code>webdriver-manager</code>.</li>
      <li><strong>Captura de Screenshot:</strong> Utiliza o Selenium em modo headless para capturar um screenshot da página inicial (primeira dobra) e salva o arquivo na pasta <code>print</code> dentro do diretório do site. O link para o screenshot é formatado para ser clicável.</li>
      <li><strong>Barra de Progresso Geral:</strong> Exibe uma barra de progresso com 16 passos por site, atualizando a descrição para indicar o site atual e a etapa em execução.</li>
      <li><strong>Verificações Realizadas (16 Passos):</strong>
        <ol>
          <li>Verificar disponibilidade do site (usando 5 métodos).</li>
          <li>Medir o tempo de resposta.</li>
          <li>Verificar redirecionamentos.</li>
          <li>Verificar certificado SSL (para URLs HTTPS).</li>
          <li>Verificar a resolução DNS do domínio.</li>
          <li>Executar teste de ping.</li>
          <li>Obter o cabeçalho Content-Type.</li>
          <li>Extrair o título da página.</li>
          <li>Analisar o conteúdo em busca de erros.</li>
          <li>Verificar a existência de <code>robots.txt</code>.</li>
          <li>Verificar a existência de <code>sitemap.xml</code>.</li>
          <li>Verificar a presença de meta refresh.</li>
          <li>Executar verificações específicas para WordPress (ex.: presença de <code>wp-content</code>, <code>wp-includes</code>, meta tag generator, endpoints <code>/wp-json/</code> e <code>/wp-admin/</code>).</li>
          <li>Salvar o conteúdo HTML para controle de versões (criando nova versão apenas se houver alterações).</li>
          <li>Medir o desempenho geral da página inicial (baseado no tempo de resposta) e atribuir uma pontuação de 0 a 100%.</li>
          <li>Capturar um screenshot da página inicial e salvar na pasta <code>print</code>.</li>
        </ol>
      </li>
      <li><strong>Score Final:</strong> O script calcula uma nota de 0 a 100% com base nos resultados (exceto o print):
        <ul>
          <li>0 a 40%: Vermelho</li>
          <li>41 a 90%: Amarelo</li>
          <li>91 a 100%: Verde Claro</li>
        </ul>
      </li>
      <li><strong>Exibição dos Resultados:</strong> Os resultados são exibidos no terminal utilizando painéis e tabelas da biblioteca <strong>Rich</strong>, incluindo um item "Print" com um link clicável para visualizar o screenshot.</li>
    </ul>
  </section>

  <section class="section">
    <h2>Requisitos</h2>
    <ul>
      <li>Python 3.6 ou superior</li>
      <li>Conexão com a Internet (para as verificações, baixar as dependências e o driver do Selenium)</li>
    </ul>
  </section>

  <section class="section">
    <h2>Instalação e Uso</h2>
    <ol>
      <li><strong>Clone o Repositório:</strong>
        <pre><code>git clone https://github.com/spalmeida/verifica-sites.git
cd verifica-sites</code></pre>
      </li>
      <li><strong>Adicione as URLs a serem verificadas:</strong>  
          Crie um arquivo chamado <code>links.txt</code> na raiz do projeto. Cada linha deve conter uma URL (linhas vazias ou iniciadas com <code>#</code> serão ignoradas).
          <pre><code>https://exemplo1.com
https://exemplo2.com</code></pre>
      </li>
      <li><strong>Execute o Script:</strong>
          <pre><code>python verificar.py</code></pre>
          O script criará automaticamente o ambiente virtual (se necessário), instalará as dependências e iniciará a verificação dos sites.
      </li>
      <li><strong>Arquivo start.bat:</strong>  
          Para facilitar a execução no Windows, você pode criar um arquivo chamado <code>start.bat</code> com o seguinte conteúdo:
          <pre><code>@echo off
python verificar.py
pause</code></pre>
          Execute o <code>start.bat</code> para iniciar o script.
      </li>
    </ol>
  </section>

  <section class="section">
    <h2>Estrutura do Projeto</h2>
    <pre><code>
verifica-sites/
├── domínios/               # Diretório onde serão salvos os resultados (HTML, prints, etc.)
├── links.txt               # Arquivo contendo as URLs a serem verificadas
├── verificar.py            # Script principal de verificação
├── start.bat               # Arquivo batch para executar o script (Windows)
└── README.md               # Documentação do projeto (este arquivo)
    </code></pre>
  </section>

  <section class="section">
    <h2>Observações</h2>
    <ul>
      <li><strong>Exibição do Screenshot:</strong>  
          O link para o screenshot é formatado com o esquema <code>file:///</code> para facilitar a abertura do arquivo. Se o seu terminal não suportar hyperlinks Rich, copie o link e cole-o no explorador de arquivos.
      </li>
      <li><strong>Ambiente Virtual:</strong>  
          Recomenda-se usar o ambiente virtual para evitar conflitos com outras dependências do sistema. O script gerencia a criação e instalação automática das dependências.
      </li>
    </ul>
  </section>

  <section class="section">
    <h2>Contribuição</h2>
    <p>
      Contribuições são bem-vindas! Se você encontrar algum bug ou tiver sugestões de melhorias, sinta-se à vontade para abrir uma issue ou enviar um pull request.
    </p>
  </section>

  <section class="section">
    <h2>Licença</h2>
    <p class="license">
      Este projeto está licenciado sob a <a href="https://opensource.org/licenses/MIT" target="_blank">MIT License</a>.
    </p>
  </section>

  <footer>
    <p>Projeto hospedado em <a href="https://github.com/spalmeida/verifica-sites/" target="_blank">https://github.com/spalmeida/verifica-sites/</a></p>
  </footer>
