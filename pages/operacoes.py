# pages/operacoes.py
import streamlit as st
from datetime import datetime, date
from SQL.database import get_db_session
from SQL.models import Operacao, Ativo
import pandas as pd
from io import BytesIO


def show_operacoes():
    st.title("Operações de Ativos")

    params = st.query_params
    editar_id = params.get("editar", [None])[0]

    if editar_id and editar_id.isdigit():
        show_edicao_operacao(int(editar_id))
        return

    tab1, tab2 = st.tabs(["Cadastro", "Lista de Operações"])

    with tab1:
        show_cadastro_operacao()

    with tab2:
        show_lista_operacoes()


def show_cadastro_operacao():
    st.subheader("Cadastro de Operação")

    session = get_db_session()
    try:
        ativos = session.query(Ativo).order_by(Ativo.ticker).all()

        if not ativos:
            st.error("Nenhum ativo cadastrado. Cadastre ativos primeiro no módulo 'Ativos'.")
            return

        with st.form("form_operacao", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                ativo_selecionado = st.selectbox(
                    "Ticker do Ativo*",
                    options=ativos,
                    format_func=lambda a: a.ticker
                )

                st.text_input("Tipo de Ativo",
                              value=ativo_selecionado.tipo_ativo,
                              disabled=True)

                data_operacao = st.date_input("Data da Operação*", datetime.now(), max_value=date.today())

            with col2:
                operacao = st.selectbox("Operação*", ['Comprar', 'Vender'])
                preco = st.number_input("Preço*", min_value=0.0, step=0.01, format="%.2f")
                quantidade = st.number_input("Quantidade*", min_value=1, step=1)

            submitted = st.form_submit_button("Salvar Operação")

            if submitted:
                try:
                    nova_operacao = Operacao(
                        id_ticker=ativo_selecionado.id,
                        tipo_operacao=operacao,
                        data_operacao=data_operacao,
                        preco=preco,
                        quantidade=quantidade
                    )
                    session.add(nova_operacao)
                    session.commit()
                    st.success("Operação cadastrada com sucesso!")
                    st.rerun()
                except Exception as e:
                    session.rollback()
                    st.error(f"Erro ao cadastrar operação: {e}")
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
    finally:
        session.remove()


def show_lista_operacoes():
    st.subheader("Lista de Operações")

    session = get_db_session()
    try:
        with st.expander("Filtros"):
            col1, col2 = st.columns(2)
            with col1:
                data_inicio = st.date_input("Data inicial", value=date(2020, 1, 1))
            with col2:
                data_fim = st.date_input("Data final", value=date.today())

        operacoes = session.query(Operacao, Ativo) \
            .join(Ativo, Operacao.id_ticker == Ativo.id) \
            .filter(Operacao.data_operacao.between(data_inicio, data_fim)) \
            .order_by(Operacao.data_operacao.desc()) \
            .all()

        if not operacoes:
            st.info("Nenhuma operação encontrada no período selecionado.")
            return

        data = []
        for op, ativo in operacoes:
            data.append({
                "Selecionar": False,
                "ID": op.id,
                "Ticker": ativo.ticker,
                "Tipo": ativo.tipo_ativo,
                "Operação": op.tipo_operacao,
                "Data": op.data_operacao.strftime("%d/%m/%Y"),
                "Preço": float(op.preco),
                "Quantidade": op.quantidade,
                "Total": float(op.preco) * op.quantidade
            })

        df = pd.DataFrame(data)

        mostrar_metricas(df)
        mostrar_opcoes_exportacao(df)

        edited_df = st.data_editor(
            df,
            column_config={
                "Selecionar": st.column_config.CheckboxColumn("Selecionar"),
                "Preço": st.column_config.NumberColumn(format="R$ %.2f"),
                "Total": st.column_config.NumberColumn(format="R$ %.2f")
            },
            disabled=["ID", "Ticker", "Tipo", "Operação", "Data", "Preço", "Quantidade", "Total"],
            hide_index=True,
            use_container_width=True
        )

        selected_rows = edited_df[edited_df["Selecionar"]]

        col1, col2, _ = st.columns(3)

        with col1:
            if st.button("📝 Editar Operação Selecionada", disabled=len(selected_rows) != 1):
                st.query_params["editar"] = int(selected_rows.iloc[0]["ID"])
                st.rerun()

        with col2:
            if st.button("🗑️ Excluir Operações Selecionadas", disabled=len(selected_rows) == 0):
                confirmar_exclusao(selected_rows, session)

    except Exception as e:
        st.error(f"Erro ao carregar operações: {e}")
    finally:
        session.remove()


def mostrar_metricas(df):
    if df.empty:
        return

    total_compras = df[df['Operação'] == 'Comprar']['Total'].sum()
    total_vendas = df[df['Operação'] == 'Vender']['Total'].sum()
    quantidade_ativos = df['Ticker'].nunique()
    total_operacoes = len(df)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Aplicado (Compras)", f"R$ {total_compras:,.2f}")
    col2.metric("Total Recebido (Vendas)", f"R$ {total_vendas:,.2f}")
    col3.metric("Ativos Diferentes", quantidade_ativos)
    col4.metric("Total de Operações", total_operacoes)


def mostrar_opcoes_exportacao(df):
    col1, col2 = st.columns(2)

    with col1:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Operações')
            writer.close()

        st.download_button(
            label="📊 Exportar para Excel",
            data=output.getvalue(),
            file_name="operacoes.xlsx",
            mime="application/vnd.ms-excel"
        )

    with col2:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📝 Exportar para CSV",
            data=csv,
            file_name="operacoes.csv",
            mime="text/csv"
        )


def confirmar_exclusao(selected_rows, session):
    st.warning("⚠️ Confirma a exclusão das operações selecionadas?")

    st.dataframe(selected_rows[["ID", "Ticker", "Tipo", "Operação", "Data", "Preço", "Quantidade"]],
                 hide_index=True)

    col1, col2, _ = st.columns(3)

    with col1:
        if st.button("✅ Confirmar Exclusão"):
            try:
                ids_to_delete = [int(row["ID"]) for _, row in selected_rows.iterrows()]
                session.query(Operacao).filter(Operacao.id.in_(ids_to_delete)).delete(synchronize_session=False)
                session.commit()
                st.success(f"{len(ids_to_delete)} operação(ões) excluída(s) com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao excluir operações: {e}")

    with col2:
        if st.button("❌ Cancelar"):
            st.rerun()


def show_edicao_operacao(operacao_id):
    st.subheader("Editar Operação")

    session = get_db_session()
    try:
        operacao, ativo = session.query(Operacao, Ativo) \
            .join(Ativo, Operacao.id_ticker == Ativo.id) \
            .filter(Operacao.id == operacao_id) \
            .first()

        if not operacao:
            st.error("Operação não encontrada!")
            st.query_params.clear()
            st.rerun()
            return

        tipos_operacao = ['Comprar', 'Vender']

        with st.form("form_edicao_operacao"):
            col1, col2 = st.columns(2)

            with col1:
                st.text_input("Ticker do Ativo", value=ativo.ticker, disabled=True)
                st.text_input("Tipo de Ativo", value=ativo.tipo_ativo, disabled=True)
                data_operacao = st.date_input("Data da Operação*", value=operacao.data_operacao, max_value=date.today())

            with col2:
                operacao_form = st.selectbox("Operação*", tipos_operacao,
                                             index=tipos_operacao.index(operacao.tipo_operacao))
                preco = st.number_input("Preço*", min_value=0.0, step=0.01, format="%.2f", value=float(operacao.preco))
                quantidade = st.number_input("Quantidade*", min_value=1, step=1, value=operacao.quantidade)

            col1, col2, _ = st.columns(3)

            with col1:
                submitted = st.form_submit_button("💾 Salvar Alterações")

            with col2:
                if st.form_submit_button("❌ Cancelar"):
                    st.query_params.clear()
                    st.rerun()

            if submitted:
                try:
                    operacao.tipo_operacao = operacao_form
                    operacao.data_operacao = data_operacao
                    operacao.preco = preco
                    operacao.quantidade = quantidade

                    session.commit()
                    st.success("Operação atualizada com sucesso!")
                    st.query_params.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao atualizar operação: {e}")

    except Exception as e:
        st.error(f"Erro ao carregar operação: {e}")
    finally:
        session.remove()