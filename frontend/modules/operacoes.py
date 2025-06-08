# frontend/pages/2_Operacoes.py

import streamlit as st
from datetime import datetime, date
import pandas as pd
import requests
from io import BytesIO

# A URL da API do backend
API_URL = "http://127.0.0.1:8000"

# --- Funções Auxiliares para Interagir com a API ---

@st.cache_data
def carregar_ativos():
    """
    Busca os ativos da API e armazena o resultado em cache para evitar
    requisições repetidas e desnecessárias.
    """
    try:
        response = requests.get(f"{API_URL}/api/ativos")
        response.raise_for_status() # Lança um erro para status HTTP 4xx/5xx
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de conexão ao buscar ativos: {e}")
        return []

def get_operacoes(data_inicio: date, data_fim: date):
    """Busca as operações dentro de um período de datas."""
    params = {"data_inicio": data_inicio.isoformat(), "data_fim": data_fim.isoformat()}
    try:
        response = requests.get(f"{API_URL}/api/operacoes", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de conexão ao buscar operações: {e}")
        return []

# --- Componentes da Página ---

def show_cadastro_operacao():
    st.subheader("Cadastro de Operação")
    
    ativos = carregar_ativos()
    
    if not ativos:
        st.error("Nenhum ativo cadastrado ou falha ao carregar. Cadastre ativos primeiro no módulo 'Ativos'.")
        return
    
    ativos_map = {a['ticker']: a for a in ativos}
    
    with st.form("form_operacao", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            ticker_selecionado = st.selectbox("Ticker do Ativo*", options=ativos_map.keys())
            ativo_obj = ativos_map[ticker_selecionado]
            st.text_input("Tipo de Ativo", value=ativo_obj['tipo_ativo'], disabled=True)
            data_operacao = st.date_input("Data da Operação*", datetime.now(), max_value=date.today())
        with col2:
            operacao = st.selectbox("Operação*", ['Comprar', 'Vender'])
            preco = st.number_input("Preço*", min_value=0.01, step=0.01, format="%.2f")
            quantidade = st.number_input("Quantidade*", min_value=1, step=1)
        
        submitted = st.form_submit_button("Salvar Operação")
        if submitted:
            payload = {
                "id_ticker": ativo_obj['id'], "tipo_operacao": operacao,
                "data_operacao": data_operacao.isoformat(), "preco": preco, "quantidade": quantidade
            }
            try:
                response = requests.post(f"{API_URL}/api/operacoes", json=payload)
                if response.status_code == 201:
                    st.success("Operação cadastrada com sucesso!")
                else:
                    st.error(f"Erro ao cadastrar: {response.json().get('detail')}")
            except requests.exceptions.RequestException as e:
                st.error(f"Erro de conexão: {e}")

def show_lista_operacoes():
    st.subheader("Lista de Operações")
    with st.expander("Filtros"):
        data_inicio = st.date_input("Data inicial", value=date(2020, 1, 1))
        data_fim = st.date_input("Data final", value=date.today())

    operacoes_data = get_operacoes(data_inicio, data_fim)
    if not operacoes_data:
        st.info("Nenhuma operação encontrada no período selecionado.")
        return

    df = pd.DataFrame(operacoes_data)
    df["Selecionar"] = False
    df["Total"] = df["preco"] * df["quantidade"]

    mostrar_metricas(df)
    mostrar_opcoes_exportacao(df)

    edited_df = st.data_editor(
        df,
        column_order=["Selecionar", "id", "ticker", "tipo_ativo", "tipo_operacao", "data_operacao", "preco", "quantidade", "Total"],
        column_config={
            "id": "ID", "ticker": "Ticker", "tipo_ativo": "Tipo Ativo", "tipo_operacao": "Operação", 
            "data_operacao": "Data", "preco": st.column_config.NumberColumn(format="R$ %.2f"), 
            "Total": st.column_config.NumberColumn(format="R$ %.2f"), "Selecionar": st.column_config.CheckboxColumn("Selecionar")
        },
        disabled=df.columns.drop("Selecionar").tolist(),
        hide_index=True, use_container_width=True
    )

    selected_rows = edited_df[edited_df["Selecionar"]]
    col1, col2, _ = st.columns([1, 1, 2])
    
    if col1.button("📝 Editar Operação Selecionada", disabled=len(selected_rows) != 1, use_container_width=True):
        st.query_params["editar"] = int(selected_rows.iloc[0]["id"])
        st.rerun()
        
    if col2.button("🗑️ Excluir Operações Selecionadas", disabled=len(selected_rows) == 0, type="primary", use_container_width=True):
        ids_para_deletar = [int(row["id"]) for _, row in selected_rows.iterrows()]
        confirmar_exclusao(ids_para_deletar)

def show_edicao_operacao(operacao_id):
    st.subheader(f"Editar Operação ID: {operacao_id}")
    try:
        response = requests.get(f"{API_URL}/api/operacoes/{operacao_id}")
        response.raise_for_status()
        operacao = response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Não foi possível carregar os dados da operação: {e}")
        if st.button("Voltar para a Lista"): st.query_params.clear()
        return

    with st.form("form_edicao"):
        st.text_input("Ticker", value=operacao['ticker'], disabled=True)
        data_op = st.date_input("Data da Operação", value=date.fromisoformat(operacao['data_operacao']))
        tipo_op = st.selectbox("Operação", ['Comprar', 'Vender'], index=['Comprar', 'Vender'].index(operacao['tipo_operacao']))
        preco = st.number_input("Preço", min_value=0.01, value=float(operacao['preco']), format="%.2f")
        quantidade = st.number_input("Quantidade", min_value=1, value=int(operacao['quantidade']))
        
        submitted = st.form_submit_button("💾 Salvar Alterações")
        if submitted:
            ativos = carregar_ativos()
            id_ticker = next((a['id'] for a in ativos if a['ticker'] == operacao['ticker']), None)
            
            payload = {
                "id_ticker": id_ticker, "tipo_operacao": tipo_op, 
                "data_operacao": data_op.isoformat(), "preco": preco, "quantidade": quantidade
            }
            try:
                put_response = requests.put(f"{API_URL}/api/operacoes/{operacao_id}", json=payload)
                if put_response.status_code == 200:
                    st.success("Operação atualizada com sucesso!")
                    st.query_params.clear()
                    st.rerun()
                else:
                    st.error(f"Erro ao salvar: {put_response.json().get('detail')}")
            except requests.exceptions.RequestException as e:
                st.error(f"Erro de conexão ao salvar: {e}")

def mostrar_metricas(df: pd.DataFrame):
    if df.empty: return
    total_compras = df[df['tipo_operacao'] == 'Comprar']['Total'].sum()
    total_vendas = df[df['tipo_operacao'] == 'Vender']['Total'].sum()
    quantidade_ativos = df['ticker'].nunique()
    total_operacoes = len(df)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Aplicado (Compras)", f"R$ {total_compras:,.2f}")
    col2.metric("Total Recebido (Vendas)", f"R$ {total_vendas:,.2f}")
    col3.metric("Ativos Diferentes", quantidade_ativos)
    col4.metric("Total de Operações", total_operacoes)

def mostrar_opcoes_exportacao(df: pd.DataFrame):
    col1, col2 = st.columns(2)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_export = df.drop(columns=["Selecionar"])
        df_export.to_excel(writer, index=False, sheet_name='Operações')
    col1.download_button(label="📊 Exportar para Excel", data=output.getvalue(), file_name="operacoes.xlsx", mime="application/vnd.ms-excel")
    
    csv = df.drop(columns=["Selecionar"]).to_csv(index=False).encode('utf-8')
    col2.download_button(label="📝 Exportar para CSV", data=csv, file_name="operacoes.csv", mime="text/csv")

def confirmar_exclusao(ids_para_deletar: list):
    payload = {"ids": ids_para_deletar}
    try:
        response = requests.post(f"{API_URL}/api/operacoes/delete", json=payload)
        if response.status_code == 200:
            st.success(response.json().get('detail'))
            st.rerun()
        else:
            st.error(f"Erro ao excluir: {response.json().get('detail')}")
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de conexão ao excluir: {e}")

# --- Ponto de Entrada da Página ---

def show_operacoes():
    """
    Função principal que controla a exibição da página de operações,
    mantendo a estrutura original do seu projeto.
    """
    st.title("Lançamento de Operações")
    editar_id = st.query_params.get("editar", [None])[0]
    if editar_id and editar_id.isdigit():
        show_edicao_operacao(int(editar_id))
    else:
        tab1, tab2 = st.tabs(["Cadastro", "Lista de Operações"])
        with tab1:
            show_cadastro_operacao()
        with tab2:
            show_lista_operacoes()
