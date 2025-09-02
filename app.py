import os # Importe a biblioteca os
from flask import Flask, render_template, abort
from fast_bitrix24 import Bitrix

# --- CONFIGURAÇÃO ---
# --- os.environ.get("WEBHOOK_URL")  ---
WEBHOOK_URL = "https://midrah.bitrix24.com.br/rest/8425/3s2oa1p7rrhwwdr0/"
if not WEBHOOK_URL:
    raise ValueError("A variável de ambiente WEBHOOK_URL não foi definida.")
ENTITY_TYPE_ID = 1138  # ID da SPA "Imóveis"

# IDs dos campos (ajustados conforme debug)
FIELD_ID_PRECO = 'ufCrm41_1756408197'
FIELD_ID_TIPO = 'ufCrm41_1756408282'
FIELD_ID_STATUS = 'ufCrm41_1756408436'
FIELD_ID_AREA = 'ufCrm41_1756408321'
FIELD_ID_ENDERECO = 'ufCrm41_1756408382'
FIELD_ID_FOTOS = 'ufCrm41_1756408463'
FIELD_ID_DESCRICAO = 'ufCrm41_1756408548'

# --- MAPAS FIXOS ---
TIPO_MAP = {
    "2845": "STUDIO",
    "2847": "1 DORM",
    "2849": "2 DORM"
}

STATUS_MAP = {
    "2851": "EM OBRA",
    "2853": "CONSTRUIDO",
    "2855": "Disponível",
    "2857": "Indisponivel"
}

try:
    b = Bitrix(WEBHOOK_URL)
except Exception as e:
    print(f"Erro ao conectar com o Bitrix24. Verifique a URL do Webhook. Erro: {e}")
    exit()

app = Flask(__name__)

# --- PROCESSAMENTO DE IMÓVEIS ---
def processar_imovel(imovel_bruto):
    if not imovel_bruto:
        return None

    tipo_id = str(imovel_bruto.get(FIELD_ID_TIPO, ''))
    status_id = str(imovel_bruto.get(FIELD_ID_STATUS, ''))

    # Fotos via urlMachine
    fotos_brutas = imovel_bruto.get(FIELD_ID_FOTOS)
    fotos_limpas = [foto.get('urlMachine') for foto in fotos_brutas] if fotos_brutas else []

    preco_bruto = imovel_bruto.get(FIELD_ID_PRECO, '0|BRL').split('|')[0]
    preco_formatado = f"{float(preco_bruto):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    # Corrige ID (pode vir como "id" ou "ID")
    imovel_id = imovel_bruto.get('id') or imovel_bruto.get('ID')

    imovel_limpo = {
        'id': imovel_id,
        'title': imovel_bruto.get('title'),
        'price': preco_formatado,
        'description': imovel_bruto.get(FIELD_ID_DESCRICAO, 'Não informado'),
        'type': TIPO_MAP.get(tipo_id, tipo_id),
        'status': STATUS_MAP.get(status_id, status_id),
        'area': imovel_bruto.get(FIELD_ID_AREA, 'Não informada'),
        'address': imovel_bruto.get(FIELD_ID_ENDERECO, 'Não informado'),
        'photos': fotos_limpas
    }
    return imovel_limpo

# --- BUSCA DE DADOS ---
def get_imoveis():
    try:
        todos_imoveis_brutos = b.get_all(
            'crm.item.list',
            params={'entityTypeId': ENTITY_TYPE_ID, 'select': ['*', 'ufCrm_*']}
        )
        print("Lista de imóveis recebida:", todos_imoveis_brutos[:2])  # DEBUG: mostra 2 itens
        imoveis_processados = [processar_imovel(imovel) for imovel in todos_imoveis_brutos]
        return [imovel for imovel in imoveis_processados if imovel]
    except Exception as e:
        print(f"Erro na API ao buscar lista de itens da SPA: {e}")
        return []

def get_imovel_by_id(item_id):
    try:
        print(f"Tentando buscar imóvel com ID {item_id}")
        resp = b.call('crm.item.get', {'entityTypeId': ENTITY_TYPE_ID, 'id': item_id})
        print("Resposta da API:", resp)  # DEBUG

        # Ajuste aqui
        imovel_bruto = resp.get('item', resp)

        return processar_imovel(imovel_bruto)
    except Exception as e:
        print(f"Erro na API ao buscar o item {item_id}: {e}")
        return None

# --- ROTAS ---
@app.route('/')
def index():
    imoveis_data = get_imoveis()
    return render_template('index.html', imoveis=imoveis_data)

@app.route('/imovel/<int:item_id>')
def detalhe_imovel(item_id):
    imovel_data = get_imovel_by_id(item_id)
    if not imovel_data:
        abort(404)
    return render_template('detalhe.html', imovel=imovel_data)

# --- EXECUÇÃO ---
if __name__ == '__main__':
    app.run(debug=True)