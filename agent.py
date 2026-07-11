"""
Agente de impressão automática - Standalone para Windows.

Escuta a coleção 'orders' do Firestore e imprime cada novo pedido
na impressora padrão. Totalmente isolado do projeto principal.

Conecta ao app web via Firestore (internet).
"""
import json
import os
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

# Quando empacotado com PyInstaller, usa a pasta do .exe
BASE_DIR = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except ImportError:
    print("ERRO: firebase-admin não instalado.")
    print("Execute: pip install -r requirements.txt")
    sys.exit(1)

from receipt_generator import (
    PRINT_ORDER,
    _get_group_for_category,
    generate_group_receipt_html,
)
from printer import print_to_default_printer

# Versão do agente - atualize a cada release enviado ao cliente
VERSION = '1.2.0'


# Variável global para o arquivo de log
_log_file = None


def init_log_file() -> Path:
    """Inicializa o arquivo de log na pasta do agente."""
    log_dir = BASE_DIR
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_path = log_dir / f'orders_log_{timestamp}.txt'
    return log_path


def log_order(order_id: str, order_data: dict, action: str = 'ENCONTRADO'):
    """
    Registra uma ordem no console e no arquivo de log.
    
    Args:
        order_id: ID do documento no Firestore
        order_data: Dados do pedido
        action: Ação realizada (ENCONTRADO, PROCESSADO, ERRO, etc.)
    """
    global _log_file
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    order_number = order_data.get('orderNumber', 'N/A')
    order_date = order_data.get('orderDate', 'N/A')
    
    # Formata a data do pedido se disponível
    if hasattr(order_date, 'timestamp'):
        order_date_str = datetime.fromtimestamp(
            order_date.timestamp(), tz=timezone.utc
        ).strftime('%Y-%m-%d %H:%M:%S UTC')
    elif isinstance(order_date, str):
        order_date_str = order_date
    else:
        order_date_str = str(order_date)
    
    # Informações principais do pedido
    customer_name = order_data.get('customerName', 'N/A')
    total = order_data.get('total', 'N/A')
    status = order_data.get('status', 'N/A')
    
    # Items do pedido
    items = order_data.get('items', [])
    items_count = len(items) if isinstance(items, list) else 0
    
    # Mensagem formatada
    log_message = (
        f"[{timestamp}] {action} - Pedido #{order_number}\n"
        f"  ID: {order_id}\n"
        f"  Cliente: {customer_name}\n"
        f"  Data do Pedido: {order_date_str}\n"
        f"  Status: {status}\n"
        f"  Total: {total}\n"
        f"  Items: {items_count}\n"
    )
    
    # Adiciona detalhes dos items se houver
    if items_count > 0:
        log_message += "  Detalhes dos Items:\n"
        for idx, item in enumerate(items[:10], 1):  # Limita a 10 items
            item_name = item.get('name', 'N/A') if isinstance(item, dict) else str(item)
            item_qty = item.get('quantity', 'N/A') if isinstance(item, dict) else 'N/A'
            item_price = item.get('price', 'N/A') if isinstance(item, dict) else 'N/A'
            log_message += f"    {idx}. {item_name} - Qtd: {item_qty} - Preço: {item_price}\n"
        if items_count > 10:
            log_message += f"    ... e mais {items_count - 10} item(s)\n"
    
    log_message += "-" * 60 + "\n"
    
    # Print no console
    # print(log_message, end='')
    
    # Escreve no arquivo de log
    if _log_file is None:
        log_path = init_log_file()
        _log_file = open(log_path, 'a', encoding='utf-8')
        print(f"[Agent] Arquivo de log criado: {log_path}")
    
    try:
        _log_file.write(log_message)
        _log_file.flush()  # Garante que seja escrito imediatamente
    except Exception as e:
        print(f"[Agent] Erro ao escrever no log: {e}")


def close_log_file():
    """Fecha o arquivo de log."""
    global _log_file
    if _log_file:
        try:
            _log_file.close()
        except Exception:
            pass
        _log_file = None


PRINTED_IDS_FILE = BASE_DIR / 'pedidos_impressos.txt'


def load_printed_ids() -> set:
    """
    Carrega os IDs dos pedidos já impressos hoje.

    Evita imprimir duas vezes quando o listener é renovado (watchdog)
    ou quando o agente é reiniciado no meio da operação.
    """
    printed: set = set()
    if not PRINTED_IDS_FILE.exists():
        return printed
    today = datetime.now().strftime('%Y-%m-%d')
    try:
        with open(PRINTED_IDS_FILE, encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) == 2 and parts[0] == today:
                    printed.add(parts[1])
        # Regrava só as linhas de hoje para o arquivo não crescer para sempre
        with open(PRINTED_IDS_FILE, 'w', encoding='utf-8') as f:
            for order_id in printed:
                f.write(f"{today}\t{order_id}\n")
    except Exception as e:
        print(f"[Agent] Aviso ao ler {PRINTED_IDS_FILE.name}: {e}")
    return printed


def mark_printed(order_id: str, printed_ids: set):
    """Marca um pedido como processado (memória + arquivo)."""
    printed_ids.add(order_id)
    try:
        with open(PRINTED_IDS_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d')}\t{order_id}\n")
    except Exception as e:
        print(f"[Agent] Aviso ao gravar {PRINTED_IDS_FILE.name}: {e}")


def load_config() -> dict:
    """
    Carrega config.json na pasta do agente.

    Suporta duas formas de autenticação Firebase (transparente ao usuário):

    1) Credenciais embutidas no config.json (recomendado - um único arquivo):
       {
         "firebase": { "type": "service_account", "project_id": "...", ... },
         "database": "a2beats-db-dev"
       }

    2) Caminho para arquivo JSON separado:
       {
         "service_account": "service-account.json",
         "database": "a2beats-db-dev"
       }

    Ordem de busca do config.json:
    1) Ao lado do executável/script (permite ajustar sem recompilar)
    2) Embutido no .exe (PyInstaller --add-data, via build-instalador.bat)
    """
    config_path = BASE_DIR / 'config.json'
    if not config_path.exists() and getattr(sys, 'frozen', False):
        bundled = Path(getattr(sys, '_MEIPASS', '')) / 'config.json'
        if bundled.exists():
            config_path = bundled
    if not config_path.exists():
        print("ERRO: config.json não encontrado.")
        print(f"Copie config.json.example para config.json em: {BASE_DIR}")
        sys.exit(1)

    with open(config_path, encoding='utf-8') as f:
        data = json.load(f)

    database = data.get('database', 'a2beats-db-dev')

    # Opção 1: Credenciais embutidas (objeto "firebase" com o JSON completo)
    firebase_creds = data.get('firebase') or data.get('firebase_credentials')
    if isinstance(firebase_creds, dict) and firebase_creds.get('type') == 'service_account':
        return {
            'credentials': firebase_creds,  # dict para credentials.Certificate()
            'database': database,
        }

    # Opção 2: Caminho para arquivo JSON
    service_account = data.get('service_account') or data.get('serviceAccount')
    if service_account:
        path = Path(service_account)
        if not path.is_absolute():
            path = BASE_DIR / path
        if path.exists():
            return {
                'credentials': str(path),  # path para credentials.Certificate()
                'database': database,
            }
        print(f"ERRO: Arquivo não encontrado: {path}")

    print("ERRO: config.json deve ter 'firebase' (objeto com credenciais) ou 'service_account' (caminho do JSON).")
    sys.exit(1)


def get_category_map(db) -> dict:
    """Busca menuCategories e retorna mapeamento categoryId -> name."""
    try:
        coll = db.collection('menuCategories')
        docs = coll.stream()
        return {doc.id: doc.to_dict().get('name', '') for doc in docs}
    except Exception as e:
        print(f"[Agent] Aviso ao buscar categorias: {e}")
        return {}


def get_table_number(db, order_data: dict) -> str:
    """
    Busca o número da mesa seguindo a estrutura:
    1. order -> comandaRef (comandaId, ex: "yn7n4JDxz25Al74jnVtH")
    2. Comanda/{comandaId} -> tableRef (ex: "/tables/SC6qbVILWGYl7yk0Tu0p")
    3. tables/{tableId} -> number (atributo 'number' da table)
    
    Retorna 'N/A' se não encontrar.
    """
    try:
        # Passo 1: Obter comandaId do comandaRef do pedido
        comanda_ref = order_data.get('comandaRef')
        if not comanda_ref:
            print("[Agent] Pedido não tem comandaRef")
            return 'N/A'
        # Extrair o ID da comanda (pode ser DocumentReference, dict, ou string)
        comanda_id = None
        
        # Tenta como DocumentReference do Firestore
        if hasattr(comanda_ref, 'id'):
            comanda_id = comanda_ref.id
        elif hasattr(comanda_ref, 'path'):
            # Se for DocumentReference, extrai o ID do path
            comanda_id = comanda_ref.path.split('/')[-1]
        elif isinstance(comanda_ref, dict):
            comanda_id = comanda_ref.get('id')
            if not comanda_id and 'path' in comanda_ref:
                comanda_id = comanda_ref['path'].split('/')[-1]
        else:
            # Se for string, pode ser o ID direto ou um path
            comanda_str = str(comanda_ref)
            if '/' in comanda_str:
                comanda_id = comanda_str.split('/')[-1]
            else:
                comanda_id = comanda_str
        
        if not comanda_id:
            print("[Agent] Não foi possível extrair comandaId do comandaRef")
            return 'N/A'
        
        # Passo 2: Buscar o documento da Comanda
        # Se comanda_ref for um DocumentReference, podemos usar diretamente
        comanda_doc = None
        if hasattr(comanda_ref, 'get'):
            # É um DocumentReference, usa diretamente
            try:
                comanda_doc = comanda_ref.get()
            except Exception as e:
                print(f"[Agent] Erro ao buscar via DocumentReference: {e}")
        
        # Se não encontrou via DocumentReference, tenta buscar pelo ID
        if not comanda_doc or not comanda_doc.exists:
            try:
                comanda_doc = db.collection('Comanda').document(comanda_id).get()
            except Exception as e:
                print(f"[Agent] Erro ao buscar pelo ID: {e}")
        
        if not comanda_doc or not comanda_doc.exists:
            print(f"[Agent] Comanda {comanda_id} não encontrada")
            return 'N/A'
        
        comanda_data = comanda_doc.to_dict()
        
        # Passo 3: Obter tableRef da comanda (pode ser "/tables/SC6qbVILWGYl7yk0Tu0p" ou DocumentReference)
        table_ref = comanda_data.get('tableRef')
        if not table_ref:
            print("[Agent] Comanda não tem tableRef")
            return 'N/A'
        
        # Extrair o ID da table
        if hasattr(table_ref, 'id'):
            table_id = table_ref.id
        elif hasattr(table_ref, 'path'):
            # Se for DocumentReference, extrai o ID do path
            table_id = table_ref.path.split('/')[-1]
        elif isinstance(table_ref, dict):
            table_id = table_ref.get('id')
            if not table_id and 'path' in table_ref:
                table_id = table_ref['path'].split('/')[-1]
        else:
            # Se for string no formato "/tables/SC6qbVILWGYl7yk0Tu0p"
            table_path = str(table_ref)
            if '/' in table_path:
                table_id = table_path.split('/')[-1]
            else:
                table_id = table_path
        
        if not table_id:
            print("[Agent] Não foi possível extrair tableId do tableRef")
            return 'N/A'
        
        # Passo 4: Buscar o documento da table e obter o atributo 'number'
        table_doc = db.collection('tables').document(table_id).get()
        if not table_doc.exists:
            print(f"[Agent] Table {table_id} não encontrada")
            return 'N/A'
        
        table_data = table_doc.to_dict()
        table_number = table_data.get('number')
        
        if table_number is not None:
            return str(table_number)
        else:
            print(f"[Agent] Table {table_id} não tem atributo 'number'")
            return 'N/A'
        
    except Exception as e:
        print(f"[Agent] Erro ao buscar número da mesa: {e}")
        import traceback
        traceback.print_exc()
        return 'N/A'


def get_product_name(db, order_data: dict) -> str:
    """
    Busca o nome do produto seguindo a estrutura:
    1. order -> productRef (productId)
    2. products/{productId} -> name (atributo 'name' do produto)
    
    Retorna 'N/A' se não encontrar.
    """
    try:
        # Primeiro tenta usar nomes já disponíveis no pedido, se houver.
        fallback_name = (
            order_data.get('productName')
            or order_data.get('product_name')
            or order_data.get('serviceName')
            or order_data.get('service_name')
            or order_data.get('name')
        )
        if fallback_name:
            return str(fallback_name)

        # Passo 1: Obter productId do productRef do pedido
        product_ref = order_data.get('productRef')
        if not product_ref:
            print("[Agent] Pedido não tem productRef")
            return 'N/A'
        
        # Extrair o ID do produto (pode ser DocumentReference, dict, ou string)
        product_id = None
        
        # Tenta como DocumentReference do Firestore
        if hasattr(product_ref, 'id'):
            product_id = product_ref.id
        elif hasattr(product_ref, 'path'):
            # Se for DocumentReference, extrai o ID do path
            product_id = product_ref.path.split('/')[-1]
        elif isinstance(product_ref, dict):
            product_id = product_ref.get('id')
            if not product_id and 'path' in product_ref:
                product_id = product_ref['path'].split('/')[-1]
        else:
            # Se for string, pode ser o ID direto ou um path
            product_str = str(product_ref)
            if '/' in product_str:
                product_id = product_str.split('/')[-1]
            else:
                product_id = product_str
        
        if not product_id:
            print("[Agent] Não foi possível extrair productId do productRef")
            return 'N/A'
        
        # Passo 2: Buscar o documento do produto
        # Se product_ref for um DocumentReference, podemos usar diretamente
        product_doc = None
        if hasattr(product_ref, 'get'):
            # É um DocumentReference, usa diretamente
            try:
                product_doc = product_ref.get()
            except Exception as e:
                print(f"[Agent] Erro ao buscar via DocumentReference: {e}")
        
        # Se não encontrou via DocumentReference, tenta buscar pelo ID
        if not product_doc or not product_doc.exists:
            try:
                product_doc = db.collection('products').document(product_id).get()
            except Exception as e:
                print(f"[Agent] Erro ao buscar pelo ID: {e}")
        
        if not product_doc or not product_doc.exists:
            print(f"[Agent] Product {product_id} não encontrado")
            return 'N/A'
        
        product_data = product_doc.to_dict()
        
        # Passo 3: Obter o atributo 'name' do produto
        product_name = product_data.get('name')
        
        if product_name:
            return str(product_name)
        else:
            print(f"[Agent] Product {product_id} não tem atributo 'name'")
            return 'N/A'
        
    except Exception as e:
        print(f"[Agent] Erro ao buscar nome do produto: {e}")
        import traceback
        traceback.print_exc()
        return 'N/A'


def process_order(order_id: str, order_data: dict, category_map: dict, db) -> bool:
    """Gera recibo e imprime. Retorna True se sucesso."""
    try:
        # Log antes de processar
        log_order(order_id, order_data, 'PROCESSANDO')
        
        # Busca o número da mesa nas coleções relacionadas
        table_number = get_table_number(db, order_data)
        # Adiciona o tableNumber ao order_data para uso no HTML
        order_data['tableNumber'] = table_number
        
        # Busca o nome do produto nas coleções relacionadas
        product_name = get_product_name(db, order_data)
        
        # Agrupa os itens por categoria
        grouped_items: dict[str, list] = {}
        items = order_data.get('items', []) or []

        category_map_recarregado = False
        for item in items:
            menu_item = item.get('menuItem', {}) or {}
            category_id = menu_item.get('categoryId', '')
            if category_id and category_id not in category_map and not category_map_recarregado:
                # Categoria criada depois que o agente iniciou: recarrega o mapa
                # do Firestore para não classificar o item como 'outros'
                print(f"[Agent] Categoria desconhecida ({category_id}), recarregando categorias...")
                category_map.update(get_category_map(db))
                category_map_recarregado = True
            category_name = category_map.get(category_id, '') or 'outros'
            group = _get_group_for_category(category_name)
            if group not in grouped_items:
                grouped_items[group] = []
            grouped_items[group].append(item)

        # Imprime um recibo separado para cada grupo que tiver itens
        total_impressoes = 0
        total_sucesso = 0
        
        for group_info in PRINT_ORDER:
            items_in_group = grouped_items.get(group_info['key'], [])
            if not items_in_group:
                continue
            
            # Gera HTML para este grupo específico
            html = generate_group_receipt_html(
                order_data,
                category_map,
                product_name=product_name,
                group_key=group_info['key'],
                group_title=group_info['title'],
                items_in_group=items_in_group,
            )
            
            # Imprime este grupo
            total_impressoes += 1
            success = print_to_default_printer(html)
            if success:
                total_sucesso += 1
                print(f"[Agent] {group_info['title']} impresso para pedido #{order_data.get('orderNumber', order_id)}")
            else:
                print(f"[Agent] Erro ao imprimir {group_info['title']} para pedido #{order_data.get('orderNumber', order_id)}")
        
        if total_sucesso == total_impressoes and total_impressoes > 0:
            log_order(order_id, order_data, f'IMPRESSO COM SUCESSO ({total_impressoes} grupo(s))')
            print(f"[Agent] Pedido #{order_data.get('orderNumber', order_id)} impresso ({total_sucesso}/{total_impressoes} grupo(s)).")
            return True
        elif total_impressoes > 0:
            log_order(order_id, order_data, f'ERRO NA IMPRESSÃO ({total_sucesso}/{total_impressoes} grupo(s))')
            return False
        else:
            log_order(order_id, order_data, 'NENHUM ITEM PARA IMPRIMIR')
            print(f"[Agent] Pedido #{order_data.get('orderNumber', order_id)} não tem itens para imprimir.")
            return False
    except Exception as e:
        log_order(order_id, order_data, f'ERRO: {str(e)}')
        print(f"[Agent] Erro ao processar pedido {order_id}: {e}")
        return False


def run_agent():
    """Inicia o agente de impressão."""
    config = load_config()

    print(f"[Agent] Iniciando agente de impressão automática (v{VERSION})...")
    print(f"[Agent] Database: {config['database']}")

    try:
        firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate(config['credentials'])
        firebase_admin.initialize_app(cred)

    db = firestore.client(database_id=config['database'] if config['database'] != 'a2beats-db-dev' else None)

    category_map = get_category_map(db)
    print(f"[Agent] {len(category_map)} categorias carregadas.")

    printed_ids = load_printed_ids()
    if printed_ids:
        print(f"[Agent] {len(printed_ids)} pedido(s) já impresso(s) hoje não serão duplicados.")

    start_time = datetime.now(timezone.utc) - timedelta(minutes=1)

    listener_health = {'last_event': None}
    # Serializa as impressões e protege a deduplicação: durante a renovação
    # do listener existem dois watches ativos por alguns instantes
    print_lock = threading.Lock()

    def on_snapshot(doc_snapshot, changes, read_time):
        """Callback chamado quando há mudanças na coleção de pedidos."""
        listener_health['last_event'] = datetime.now(timezone.utc)
        # Log de todas as mudanças detectadas
        print(f"\n[Agent] Snapshot recebido - {len(changes)} mudança(s) detectada(s)")

        # Processa todas as mudanças
        for change in changes:
            change_type = change.type.name
            doc = change.document

            if not doc.exists:
                continue

            data = doc.to_dict()
            order_id = doc.id

            # Log de TODAS as ordens encontradas (independente do tipo de mudança)
            log_order(order_id, data, f'MUDAÇA: {change_type}')

            # Processa apenas novos pedidos (ADDED)
            if change_type != 'ADDED':
                continue

            # Verifica se o pedido é recente (após start_time)
            order_date = data.get('orderDate')
            if order_date and hasattr(order_date, 'timestamp'):
                doc_time = datetime.fromtimestamp(order_date.timestamp(), tz=timezone.utc)
                if doc_time < start_time:
                    log_order(order_id, data, 'IGNORADO (pedido antigo)')
                    continue

            with print_lock:
                # Pula pedidos já processados (reentregues por renovação
                # do listener ou reinício do agente)
                if order_id in printed_ids:
                    log_order(order_id, data, 'IGNORADO (já impresso)')
                    continue
                mark_printed(order_id, printed_ids)
                # Processa o pedido (gera recibo e imprime)
                process_order(order_id, data, category_map, db)

    orders_ref = db.collection('orders')
    from google.cloud.firestore_v1.base_query import FieldFilter
    from google.cloud.firestore_v1 import Query
    
    # Este bloco todo busca TODAS as orders no Firestore e logar no console e no arquivo de log.
    # # Busca inicial: obtém TODAS as orders para log (sem filtro de data)
    # print("[Agent] Buscando TODAS as orders no Firestore...")
    # try:
    #     # Stream direto da coleção: traz todos os documentos de 'orders'
    #     initial_docs = orders_ref.stream()
    #     initial_count = 0
    #     print("[Agent] Lista de orders (busca inicial - TODAS as orders encontradas):")
    #     for doc in initial_docs:
    #         initial_count += 1
    #         data = doc.to_dict()
    #         # Print simples da lista de pedidos encontrados
    #         print(
    #             f"  - ID: {doc.id} | "
    #             f"Pedido: {data.get('orderNumber', 'N/A')} | "
    #             f"Status: {data.get('status', 'N/A')} | "
    #             f"Total: {data.get('total', 'N/A')}"
    #         )
    #         log_order(doc.id, data, 'BUSCA INICIAL')
        
    #     print(f"[Agent] {initial_count} pedido(s) recente(s) encontrado(s) na busca inicial.")
    # except Exception as e:
    #     print(f"[Agent] Aviso ao buscar pedidos iniciais: {e}")
    
    # Configura listener em tempo real
    def subscribe(since):
        """(Re)cria o listener de pedidos a partir do instante informado."""
        query = orders_ref.where(
            filter=FieldFilter('orderDate', '>', since)
        ).order_by('orderDate', direction=Query.ASCENDING)
        return query.on_snapshot(on_snapshot)

    watch = subscribe(start_time)

    print("[Agent] Escutando novos pedidos em tempo real...")
    print("[Agent] Conectado ao app web via Firestore.")
    print("[Agent] Pressione Ctrl+C para encerrar.")
    print("-" * 50)

    # Watchdog: a API do Firestore não avisa quando o listener morre
    # (queda de internet, token expirado). Renovamos a inscrição
    # preventivamente a cada RENEW_INTERVAL; a janela de 5 min combinada
    # com a deduplicação garante que nenhum pedido se perde nem duplica.
    RENEW_INTERVAL = 15 * 60   # segundos entre renovações do listener
    RETRY_MAX = 5 * 60         # espera máxima entre tentativas com falha
    last_renew = time.monotonic()
    retry_delay = 30

    while True:
        time.sleep(1)
        if time.monotonic() - last_renew < RENEW_INTERVAL:
            continue
        try:
            # Cria o novo watch antes de cancelar o antigo para nunca
            # ficar sem listener; a sobreposição breve é coberta pelo lock
            new_watch = subscribe(datetime.now(timezone.utc) - timedelta(minutes=5))
            try:
                watch.unsubscribe()
            except Exception:
                pass
            watch = new_watch
            last_renew = time.monotonic()
            retry_delay = 30
            last_event = listener_health['last_event']
            if last_event:
                minutos = int((datetime.now(timezone.utc) - last_event).total_seconds() // 60)
                print(f"[Agent] Listener renovado (último evento: {minutos} min atrás).")
            else:
                print("[Agent] Listener renovado (nenhum evento recebido ainda).")
        except Exception as e:
            print(f"[Agent] Falha ao renovar listener: {e}")
            print(f"[Agent] O listener atual segue ativo; nova tentativa em {retry_delay}s.")
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, RETRY_MAX)


if __name__ == '__main__':
    try:
        run_agent()
    except KeyboardInterrupt:
        print("\n[Agent] Encerrado pelo usuário.")
        close_log_file()
        sys.exit(0)
    except Exception as e:
        print(f"[Agent] Erro fatal: {e}")
        close_log_file()
        sys.exit(1)
