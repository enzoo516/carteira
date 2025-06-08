# frontend/pages/ativos.py - CÓDIGO COMPLETO E MODIFICADO

import streamlit as st
import requests  # <-- A nova forma de comunicação
import pandas as pd

API_URL = "http://127.0.0.1:8000"  # O endereço do seu backend

# As suas funções originais são mantidas, mas o CONTEÚDO delas muda.
def show_ativos():
    st.title("Gestão de Ativos")
    tab1, tab2 = st.tabs(["Cadastro", "Lista de Ativos"])
    with tab1:
        show_cadastro_ativo()
    with tab2:
        show_lista_ativos()

def show_cadastro_ativo():
    st.subheader("Cadastro de Ativo")
    tipos_ativo = ['FII', 'ETF', 'Ação']
    with st.form("form_ativo", clear_on_submit=True):
        ticker = st.text_input("Ticker do Ativo* (Ex: XPML11)").strip().upper()
        tipo_ativo = st.selectbox("Tipo de Ativo*", tipos_ativo)
        submitted = st.form_submit_button("Salvar Ativo")

        if submitted:
            if not ticker:
                st.error("O ticker do ativo é obrigatório!")
                return

            # Em vez de chamar o banco, chamamos a API
            payload = {"ticker": ticker, "tipo_ativo": tipo_ativo}
            try:
                response = requests.post(f"{API_URL}/api/ativos", json=payload)
                if response.status_code == 200: # FastAPI retorna 200 por padrão no POST
                    st.success("Ativo cadastrado com sucesso!")
                else:
                    # Mostra o erro vindo diretamente da API
                    st.error(f"Erro: {response.json().get('detail')}")
            except requests.exceptions.RequestException as e:
                st.error(f"Erro de conexão com o backend: {e}")

def show_lista_ativos():
    st.subheader("Lista de Ativos Cadastrados")
    try:
        # Em vez de chamar session.query, chamamos a API
        response = requests.get(f"{API_URL}/api/ativos")
        if response.status_code != 200:
            st.error("Falha ao carregar ativos do backend.")
            return

        ativos = response.json()
        if not ativos:
            st.info("Nenhum ativo cadastrado ainda.")
            return
        
        # O resto da lógica para exibir a tabela é quase a mesma
        df = pd.DataFrame(ativos)
        df["Excluir"] = False

        edited_df = st.data_editor(
            df,
            column_config={ "id": "ID", "ticker": "Ticker", "tipo_ativo": "Tipo", "Excluir": st.column_config.CheckboxColumn("Excluir?")},
            disabled=["id", "ticker", "tipo_ativo"], hide_index=True, use_container_width=True
        )

        if st.button("Excluir Selecionados", type="primary"):
            ids_para_deletar = [row["id"] for i, row in edited_df.iterrows() if row["Excluir"]]
            if not ids_para_deletar:
                st.warning("Nenhum ativo selecionado para exclusão!")
                return
            
            # Em vez de chamar session.delete, chamamos a API
            payload = {"ids": ids_para_deletar}
            try:
                del_response = requests.post(f"{API_URL}/api/ativos/delete", json=payload)
                if del_response.status_code == 200:
                    st.success(del_response.json().get('detail'))
                    st.rerun()
                else:
                    st.error(f"Erro ao excluir: {del_response.json().get('detail')}")
            except requests.exceptions.RequestException as e:
                st.error(f"Erro de conexão ao excluir: {e}")

    except requests.exceptions.RequestException as e:
        st.error(f"Erro de conexão com o backend: {e}")