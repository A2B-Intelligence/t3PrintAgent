"""
Gera HTML de recibo para impressão, compatível com o formato do receipt-printer.ts
"""
from datetime import datetime
from typing import Any

GROUP_CATEGORIES = {
    'cozinha': [
        'entradas quentes', 'poke bolw', 'yakisobas', 'sobremesas',
        'rodizio premium - cozinha', 'Jow (x6)', 'Combinados', 'Pratos Quentes',
    ],
    'sushibar': [
        'entradas', 'hossomakis (x4)', 'uramakis (x4)', 'temaki',
        'rodizio premium - sushibar', 'Sushis e Sashimis (x5)',
    ],
    'sushibarhot': ['hots (x4)'],
    'bar': ['bebidas', 'bebidas alcoólicas', 'bebidas não alcoólicas'],
}

PRINT_ORDER = [
    {'key': 'cozinha', 'title': '--- PARA A COZINHA ---'},
    {'key': 'sushibar', 'title': '--- PARA O SUSHIBAR ---'},
    {'key': 'sushibarhot', 'title': '--- PARA O SUSHIBAR (HOTS) ---'},
    {'key': 'bar', 'title': '--- PARA O BAR ---'},
    {'key': 'outros', 'title': '--- OUTROS ---'},
]


def _get_group_for_category(category_name: str) -> str:
    if not category_name:
        return 'outros'
    name_lower = category_name.lower().strip()
    for group, categories in GROUP_CATEGORIES.items():
        # Compara em minúsculas dos dois lados para não depender de como
        # a categoria foi digitada aqui ou no banco
        if any(name_lower == c.lower().strip() for c in categories):
            return group
    return 'outros'


def _parse_order_date(order_date: Any) -> datetime:
    if order_date is None:
        return datetime.now()
    if hasattr(order_date, 'timestamp'):
        return datetime.fromtimestamp(order_date.timestamp())
    if isinstance(order_date, datetime):
        return order_date
    if isinstance(order_date, str):
        try:
            return datetime.fromisoformat(order_date.replace('Z', '+00:00'))
        except ValueError:
            return datetime.now()
    return datetime.now()


def generate_group_receipt_html(
    order: dict[str, Any],
    category_map: dict[str, str],
    product_name: str,
    group_key: str,
    group_title: str,
    items_in_group: list,
) -> str:
    """
    Gera HTML de recibo para um grupo específico (COZINHA, SUSHIBAR, etc.).
    Cada recibo contém todos os dados do pedido + apenas os itens do grupo.
    """
    customer = order.get('customer', {}) or {}
    order_number = order.get('orderNumber', 'N/A')
    table_number = order.get('tableNumber') or 'N/A'
    order_type = order.get('orderType') or 'Comanda'

    order_date = _parse_order_date(order.get('orderDate'))
    date_str = order_date.strftime('%d/%m/%Y')
    time_str = order_date.strftime('%H:%M')

    html = f'''<html>
<head>
  <title>Pedido #{order_number} - {group_title}</title>
  <style>
    @page {{
      margin: 0;
    }}
    body {{
      font-family: Arial, sans-serif;
      font-size: 35px;
      line-height: 1.2;
      width: 80mm;
      margin: 0 auto;
      padding: 1mm;
    }}
    .center {{ text-align: center; }}
    .right {{ text-align: right; }}
    .bold {{ font-weight: bold; }}
    .large {{ font-size: 48px; }}
    .small {{ font-size: 25px; }}
    .line {{
      border-bottom: 1px dashed #000;
      margin: 2px 0;
    }}
    .flex {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
    }}
    .item-row {{
      margin-bottom: 1px;
    }}
    .observation {{
      font-size: 35px;
      margin-left: 10px;
      margin-top: 2px;
    }}
    .group-title {{
      font-weight: bold;
      font-size: 35px;
      margin: 0px 0 5px 0;
      text-align: center;
    }}
    .group-section {{
      margin-bottom: 1px;
    }}
  </style>
</head>
<body>
  <div class="center bold large">T3</div>
  <br>
  <div class="bold center">--- IMPRESSÃO AUTOMÁTICA ---</div>
  <div class="bold">Pedido #{order_number}</div>
  <div class="bold">Mesa: {table_number}</div>
  <div class="bold">Serviço: {product_name}</div>
  <div class="bold">{'Cliente (Retirada)' if order_type == 'PDV' else 'Cliente'}</div>
  <div>Nome: {customer.get('name', '')}</div>'''
    
    if order_type != 'PDV' and customer.get('address'):
        html += f'  <div>Endereco: {customer["address"]}</div>\n'
    
    html += f'''
  <div class="line"></div>
  <div class="flex">
    <span class="bold">Itens do pedido<br></span>
    <span>{date_str} {time_str}<br></span>
  </div>
  <br>
  <div class="group-section">
    <div class="group-title">{group_title}</div>
    <div class="flex bold">
      <span>Qtd</span>
      <span>Item</span>
      <span>Preço</span>
    </div>'''
    
    for item in items_in_group:
        qty = item.get('quantity', 1)
        price = item.get('selectedPrice', 0)
        item_total = price * qty
        name = (item.get('menuItem') or {}).get('name', 'Item')
        obs = item.get('observation', '')
        html += f'''
    <div class="item-row">
      <div class="flex">
        <span>{qty}x</span>
        <span style="flex: 1; margin: 0 10px;">{name}</span>
        <span>R$ {item_total:.2f}</span>
      </div>'''
        if obs:
            html += f'      <div class="observation">Obs: {obs}</div>'
        html += '''
    </div>'''
    
    html += '''
  </div>
  <div class="line"></div>
  <div class="center small">Desenvolvido por A2B Negócios Inteligentes</div>
  <br><br>
</body>
</html>'''
    return html


def generate_receipt_html(
    order: dict[str, Any],
    category_map: dict[str, str],
    product_name: str = 'N/A',
    imprimir_detalhado: bool = True,
) -> str:
    items = order.get('items', []) or []
    customer = order.get('customer', {}) or {}
    order_number = order.get('orderNumber', 'N/A')
    table_number = order.get('tableNumber') or 'N/A'
    order_type = order.get('orderType') or 'Comanda'
    payment_methods = order.get('paymentMethods', [])
    observation = order.get('observation', '')
    coupon = order.get('coupon')

    order_date = _parse_order_date(order.get('orderDate'))
    date_str = order_date.strftime('%d/%m/%Y')
    time_str = order_date.strftime('%H:%M')

    grouped_items: dict[str, list] = {}
    for item in items:
        menu_item = item.get('menuItem', {}) or {}
        category_id = menu_item.get('categoryId', '')
        category_name = category_map.get(category_id, '') or 'outros'
        group = _get_group_for_category(category_name)
        if group not in grouped_items:
            grouped_items[group] = []
        grouped_items[group].append(item)

    subtotal = sum(
        (item.get('selectedPrice') or 0) * (item.get('quantity') or 0)
        for item in items
    )
    total = order.get('total') or subtotal

    html = f'''<html>
<head>
  <title>Pedido #{order_number}</title>
  <style>
    @page {{
      margin: 0;
    }}
    body {{
      font-family: Arial, sans-serif;
      font-size: 35px;
      line-height: 1.2;
      width: 80mm;
      margin: 0 auto;
      padding: 1mm;
    }}
    .center {{ text-align: center; }}
    .right {{ text-align: right; }}
    .bold {{ font-weight: bold; }}
    .large {{ font-size: 48px; }}
    .small {{ font-size: 25px; }}
    .line {{
      border-bottom: 1px dashed #000;
      margin: 2px 0;
    }}
    .flex {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
    }}
    .item-row {{
      margin-bottom: 1px;
    }}
    .observation {{
      font-size: 35px;
      margin-left: 10px;
      margin-top: 2px;
    }}
    .group-title {{
      font-weight: bold;
      font-size: 35px;
      margin: 0px 0 5px 0;
      text-align: center;
    }}
    .group-section {{
      margin-bottom: 1px;
    }}
  </style>
</head>
<body>'''

    if imprimir_detalhado:
        html += f'''
  <div class="center bold large">T3</div>
  <br>
  <div class="bold center">--- IMPRESSÃO AUTOMÁTICA ---</div>
  <div class="bold">Pedido #{order_number}</div>
  <div class="bold">Mesa: {table_number}</div>
  <div class="bold">Serviço: {product_name}</div>
  <div class="bold">{'Cliente (Retirada)' if order_type == 'PDV' else 'Cliente'}</div>
  <div>Nome: {customer.get('name', '')}</div>'''
    if order_type != 'PDV' and customer.get('address'):
        html += f'  <div>Endereco: {customer["address"]}</div>\n'
    html += f'''
  <div class="line"></div>
  <div class="flex">
    <span class="bold">Itens do pedido<br></span>
    <span>{date_str} {time_str}<br></span>
  </div>
  <br>'''

    for group_info in PRINT_ORDER:
        items_in_group = grouped_items.get(group_info['key'], [])
        if not items_in_group:
            continue
        html += f'''
  <div class="group-section">
    <div class="group-title">{group_info['title']}</div>
    <div class="flex bold">
      <span>Qtd</span>
      <span>Item</span>
      <span>Preço</span>
    </div>'''
        for item in items_in_group:
            qty = item.get('quantity', 1)
            price = item.get('selectedPrice', 0)
            item_total = price * qty
            name = (item.get('menuItem') or {}).get('name', 'Item')
            obs = item.get('observation', '')
        html += f'''
    <div class="item-row">
        <div class="flex">
            <span>{qty}x</span>
            <span style="flex: 1; margin: 0 10px;">{name}</span>
            <span>R$ {item_total:.2f}</span>
        </div>
        <div class="center small">Desenvolvido por A2B Negócios Inteligentes</div>
    </div>'''

#     if imprimir_detalhado:
#         html += f'''
#   <div class="line"></div>
#   <div class="flex">
#     <span>Subtotal</span>
#     <span>R$ {subtotal:.2f}</span>
#   </div>'''
#     html += f'''
#   <div class="flex bold">
#     <span>Total</span>
#     <span>R$ {total:.2f}</span>
#   </div>'''
#     html += '''
#   <br><br>'''
#     html += '''
# </body>
# </html>'''
    return html
