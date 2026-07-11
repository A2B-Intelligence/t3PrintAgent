# Agente de Impressão Automática

Aplicação **standalone** para Windows que escuta novos pedidos do app web e imprime automaticamente na impressora padrão.

**Totalmente isolada** – não depende do projeto principal. Pode ser copiada para qualquer máquina Windows.

## Requisitos

- Windows com impressora configurada como padrão
- Python 3.10+ (ou use o .exe gerado)
- [SumatraPDF](https://www.sumatrapdfreader.org/) instalado ou `SumatraPDF.exe` na pasta
- Acesso à internet (conexão com Firestore)

## Instalação Rápida

### 1. Copie a pasta `print-agent` para a máquina Windows

A pasta deve conter:
- `agent.py`, `printer.py`, `receipt_generator.py`
- `requirements.txt`
- `config.json.example`
- `run.bat`

### 2. Obtenha a Service Account do Firebase

1. [Firebase Console](https://console.firebase.google.com) → Seu projeto → Configurações (ícone engrenagem) → Contas de serviço
2. Clique em **Gerar nova chave privada** → Baixe o JSON

### 3. Configure (duas opções – transparente ao usuário)

**Opção A – Credenciais embutidas (recomendado, um único arquivo):**

Copie `config-embutido.json.example` para `config.json`. Abra o JSON baixado do Firebase e copie todo o conteúdo para a chave `"firebase"`:

```json
{
  "database": "a2beats-db-dev",
  "firebase": {
    "type": "service_account",
    "project_id": "a2b-eats-bl3m3",
    "private_key_id": "...",
    "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
    "client_email": "firebase-adminsdk-xxx@a2b-eats-bl3m3.iam.gserviceaccount.com",
    ...
  }
}
```

O usuário final só precisa desse `config.json` – sem arquivos extras.

**Atalho:** Na máquina de desenvolvimento, execute `python gerar-config.py firebase-adminsdk-xxx.json` – o script cria o `config.json` automaticamente.

**Opção B – Arquivo JSON separado:**

Copie `config.json.example` para `config.json`. Coloque o JSON baixado como `service-account.json` na mesma pasta:

```json
{
  "service_account": "service-account.json",
  "database": "a2beats-db-dev"
}
```

### 4. Instale dependências e execute

**Opção A – Com Python instalado:**
- Duplo-clique em `run.bat` (cria o venv automaticamente na primeira vez, veja abaixo)
- Ou manualmente, veja [Ambiente virtual (venv)](#ambiente-virtual-venv)

**Opção B – Executável (.exe):**
- Na máquina de desenvolvimento: execute `build.bat`
- Copie `dist/PrintAgent.exe` para a máquina Windows
- Coloque na mesma pasta: `config.json`, `service-account.json`
- Execute `PrintAgent.exe`

## Ambiente virtual (venv)

O `run.bat` e o `run-silent.bat` já criam e ativam o venv automaticamente — na maioria dos casos não é preciso fazer nada manualmente. Use os passos abaixo só se for rodar `agent.py` direto, sem passar pelos `.bat`.

### Criar o venv (uma vez só)

```bat
cd /d caminho\para\t3PrintAgent
python -m venv venv
```

### Ativar o venv

- **cmd:** `venv\Scripts\activate.bat`
- **PowerShell:** `venv\Scripts\Activate.ps1`
  - Se der erro de política de execução, rode antes: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

O prompt passa a mostrar `(venv)` quando estiver ativo.

### Instalar dependências

```bat
pip install -r requirements.txt
```

### Rodar o agente

```bat
python agent.py
```

### Desativar

```bat
deactivate
```

## Executar em segundo plano

- **run-silent.bat** – inicia sem janela (usa pythonw)
- **Iniciar com o Windows** – crie um atalho de `iniciar-com-windows.vbs` ou `run-silent.bat` na pasta de Inicialização:
  - `Win+R` → `shell:startup` → Enter
  - Cole o atalho na pasta que abrir

## Conexão com o app web

O agente conecta ao **Firestore** (Firebase) na internet. O app web grava os pedidos na coleção `orders`. O agente escuta em tempo real e imprime cada novo pedido.

Não é necessário estar na mesma rede ou ter acesso às pastas do projeto.

## Estrutura da pasta

```
print-agent/
├── agent.py                  # Ponto de entrada
├── printer.py                # Impressão silenciosa
├── receipt_generator.py      # Geração do recibo
├── config.json               # Configuração (contém credenciais se usar opção embutida)
├── config.json.example       # Modelo com caminho para arquivo
├── config-embutido.json.example  # Modelo com credenciais embutidas
├── requirements.txt
├── run.bat               # Iniciar com console
├── run-silent.bat        # Iniciar sem janela
├── build.bat             # Gerar PrintAgent.exe
└── README.md
```

## Instalador .exe com credenciais embutidas (recomendado para novos clientes)

Gera um único `PrintAgent-Setup-vX.Y.Z.exe`: o usuário leigo instala com "Avançar → Avançar → Concluir" e **não tem acesso ao config.json** — as credenciais ficam embutidas dentro do executável.

### Preparar a máquina Windows de build (uma vez só)

1. Instale [Python 3.10+](https://www.python.org/) (marque "Add to PATH")
2. Instale o [Inno Setup 6](https://jrsoftware.org/isdl.php) (gratuito, opções padrão)
3. Clone/copie esta pasta do projeto

### Gerar o instalador

1. Coloque na pasta do projeto:
   - o JSON da service account do Firebase
   - `SumatraPDF.exe` (versão portable)
2. Gere o config: `python gerar-config.py sua-service-account.json`
3. Rode `build-instalador.bat`

Sai o `PrintAgent-Setup-vX.Y.Z.exe`. **Envie só esse arquivo ao cliente.**

### O que o instalador faz no cliente

- Instala em `%LocalAppData%\PrintAgent` (não pede senha de administrador)
- Instala o SumatraPDF junto (impressão silenciosa)
- Cria atalho no Menu Iniciar (+ área de trabalho, opcional)
- Opção "Iniciar automaticamente com o Windows" (marcada por padrão)
- Para **atualizar**: basta enviar um novo Setup e instalar por cima — ele encerra o agente sozinho e preserva o histórico de impressões do dia

**Nota de segurança:** embutir no .exe esconde as credenciais do usuário comum, mas não é criptografia — alguém técnico com ferramentas consegue extrair. A proteção real é dar à service account só as permissões mínimas no Firestore. Se um dia precisar trocar a chave, gere um novo config.json + instalador e reinstale.

## Atualização do cliente (deploy de nova versão)

O cliente roda a partir do código-fonte (`run.bat` + venv). Para enviar uma nova versão:

### Na máquina de desenvolvimento

1. Faça as alterações no código (ex.: novas categorias em `GROUP_CATEGORIES`)
2. Atualize a constante `VERSION` em `agent.py` (ex.: `1.1.0` → `1.2.0`)
3. Gere o pacote:
   - **macOS/Linux:** `./criar-atualizacao.sh`
   - **Windows:** `criar-atualizacao.bat`
4. Envie o `PrintAgent-Update-vX.Y.Z.zip` ao cliente (WhatsApp, e-mail, etc.)

### Na máquina do cliente

1. Extrair a pasta `update` do ZIP **para dentro** da pasta do PrintAgent (a que contém `agent.py` e `config.json`)
2. Duplo-clique em `update\atualizar.bat`

O atualizador faz tudo sozinho: encerra o agente, faz backup da versão atual em `backup\`, copia os novos arquivos (sem tocar no `config.json`) e reinicia o agente. Para reverter, basta copiar os arquivos de `backup\<data>` de volta.

### Categorias novas no cardápio

O mapeamento categoria → local de impressão (`GROUP_CATEGORIES` em `receipt_generator.py`) é fixo no código. **Sempre que o restaurante criar uma categoria nova**, adicione-a à lista do grupo certo e gere uma atualização — caso contrário os itens dela saem em "OUTROS". A comparação ignora maiúsculas/minúsculas e espaços nas pontas, mas o nome precisa ser idêntico ao cadastrado no app web.

## Solução de problemas

**"config.json não encontrado"** – Copie `config.json.example` para `config.json` e configure.

**"SumatraPDF não encontrado"** – Instale em sumatrapdfreader.org ou coloque `SumatraPDF.exe` na pasta.

**"Arquivo não encontrado" (service account)** – Verifique o caminho em `config.json`. Use nome do arquivo se estiver na mesma pasta.

**Pedidos não imprimem** – Confirme que o `database` em `config.json` é o mesmo do app web (`a2beats-db-dev`).

**Pedido não reimprime nem reiniciando o agente** – O agente registra os pedidos já impressos no dia em `pedidos_impressos.txt` (na pasta do agente) para nunca imprimir duplicado. Para forçar a reimpressão de um pedido, apague a linha com o ID dele nesse arquivo e reinicie o agente.
