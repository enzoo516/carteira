# pages/ativos.py
import streamlit as st
from SQL.database import get_db_session
from SQL.models import Ativo


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
        col1, col2 = st.columns(2)

        with col1:
            ticker = st.text_input("Ticker do Ativo* (Ex: XPML11)").strip().upper()

        with col2:
            tipo_ativo = st.selectbox("Tipo de Ativo*", tipos_ativo)

        submitted = st.form_submit_button("Salvar Ativo")

        if submitted:
            if not ticker:
                st.error("O ticker do ativo é obrigatório!")
                return

            session = get_db_session()
            try:
                if session.query(Ativo).filter(Ativo.ticker == ticker).first():
                    st.error("Este ticker já está cadastrado!")
                    return

                novo_ativo = Ativo(ticker=ticker, tipo_ativo=tipo_ativo)
                session.add(novo_ativo)
                session.commit()
                st.success("Ativo cadastrado com sucesso!")
                st.rerun()
            except Exception as e:
                session.rollback()
                st.error(f"Erro ao cadastrar ativo: {e}")
            finally:
                session.remove()


def show_lista_ativos():
    st.subheader("Lista de Ativos Cadastrados")

    session = get_db_session()
    try:
        ativos = session.query(Ativo).order_by(Ativo.ticker).all()

        if not ativos:
            st.info("Nenhum ativo cadastrado ainda.")
            return

        data = []
        for ativo in ativos:
            data.append({
                "ID": ativo.id,
                "Ticker": ativo.ticker,
                "Tipo": ativo.tipo_ativo,
                "Qtd. Operações": len(ativo.operacoes)
            })

        st.dataframe(
            data,
            column_config={
                "ID": st.column_config.NumberColumn("ID", width="small"),
                "Ticker": "Ticker",
                "Tipo": "Tipo de Ativo",
                "Qtd. Operações": "Quantidade de Operações"
            },
            hide_index=True,
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Erro ao carregar ativos: {e}")
    finally:
        session.remove()