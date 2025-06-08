# Pages/informacoes.py

import streamlit as st
import pandas as pd

from SQL.database import get_db_session
from SQL.models import Ativo, Operacao

from controllers.api_bcb import get_cdi_accumulated
from controllers.yahoo_finance import get_ativo_info, get_dividendos_12m

def show_informacoes():
    st.title("📊 Informações dos Ativos")

    session = get_db_session()

    try:
        ativos_db = session.query(Ativo).all()

        if not ativos_db:
            st.warning("Nenhum ativo cadastrado. Cadastre ativos primeiro no módulo 'Ativos'.")
            return

        cdi_acumulado = get_cdi_accumulated()

        dados_ativos = []
        historicos = {}

        for ativo in ativos_db:
            info = get_ativo_info(ativo.ticker)

            if info:
                valor_investido = 10000  # Substituir por valor real do banco
                valor_atual = valor_investido * (1 + info['Rendimento 6M (%)'] / 100)

                dados_ativos.append({
                    'Ticker': ativo.ticker,
                    'Tipo': ativo.tipo_ativo,
                    'Preço Atual': info['Preço Atual'],
                    'Total Investido': valor_investido,
                    'Valor Atual': valor_atual,
                    'Rendimento Total (%)': info['Rendimento 6M (%)'],
                    'Rendimento Mês (%)': info['Rendimento Mês (%)'],
                    'Rendimento Dia (%)': info['Rendimento Dia (%)'],
                    'Dividendos': info['Dividendos 12M'],
                    'CDI Acumulado (%)': cdi_acumulado,
                    'Performance vs CDI (%)': info['Rendimento 6M (%)'] - cdi_acumulado
                })

                historicos[ativo.ticker] = info['Histórico']

        df_ativos = pd.DataFrame(dados_ativos)

        # Filtros
        with st.expander("🔍 Filtros", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                ticker_filtro = st.multiselect(
                    "Selecione os Tickers",
                    options=df_ativos['Ticker'].unique(),
                    default=df_ativos['Ticker'].unique()
                )
            with col2:
                tipo_filtro = st.multiselect(
                    "Tipo de Ativo",
                    options=df_ativos['Tipo'].unique(),
                    default=df_ativos['Tipo'].unique()
                )

        df_filtrado = df_ativos[
            df_ativos['Ticker'].isin(ticker_filtro) &
            df_ativos['Tipo'].isin(tipo_filtro)
        ]

        # Métricas Gerais
        st.subheader("📈 Desempenho da Carteira")

        if not df_filtrado.empty:
            total_investido = df_filtrado['Total Investido'].sum()
            valor_atual = df_filtrado['Valor Atual'].sum()
            rend_total = ((valor_atual - total_investido) / total_investido) * 100
            dividendos = df_filtrado['Dividendos'].sum()

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Investido", f"R$ {total_investido:,.2f}")
            with col2:
                st.metric("Valor Atual", f"R$ {valor_atual:,.2f}", f"{rend_total:.2f}%")
            with col3:
                st.metric("Rendimento Total", f"{rend_total:.2f}%", f"vs {cdi_acumulado:.2f}% CDI")
            with col4:
                st.metric("Dividendos Recebidos", f"R$ {dividendos:,.2f}")

        st.subheader("📋 Resumo por Ativo")

        format_dict = {
            'Preço Atual': 'R${:,.2f}',
            'Total Investido': 'R${:,.2f}',
            'Valor Atual': 'R${:,.2f}',
            'Rendimento Total (%)': '{:.2f}%',
            'Rendimento Mês (%)': '{:.2f}%',
            'Rendimento Dia (%)': '{:.2f}%',
            'Dividendos': 'R${:,.2f}',
            'CDI Acumulado (%)': '{:.2f}%',
            'Performance vs CDI (%)': '{:.2f}%'
        }

        styled_df = df_filtrado.style.format(format_dict)

        selected_ticker = st.data_editor(
            styled_df,
            column_config={
                "Ticker": st.column_config.TextColumn("Ticker", width="small"),
                "Performance vs CDI (%)": st.column_config.ProgressColumn(
                    "Performance vs CDI",
                    format="%.2f%%",
                    min_value=-50,
                    max_value=50,
                )
            },
            disabled=df_filtrado.columns.tolist(),
            hide_index=True,
            use_container_width=True,
            key="tabela_ativos"
        )

        # Detalhes do Ativo Selecionado
        if not selected_ticker.empty:
            selected_row = df_filtrado.iloc[0]
            ticker = selected_row['Ticker']

            st.subheader(f"📌 Detalhes do Ativo {ticker}")

            st.line_chart(historicos[ticker]['Close'].rename('Preço (R$)'))

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Preço Atual", f"R$ {selected_row['Preço Atual']:,.2f}")
                st.metric("Rendimento 6M", f"{selected_row['Rendimento Total (%)']:.2f}%")
            with col2:
                st.metric("Dividendos 12M", f"R$ {selected_row['Dividendos']:,.2f}")
                st.metric("DY", f"{selected_row['Dividendos']/selected_row['Preço Atual']*100:.2f}%")
            with col3:
                st.metric("CDI Acumulado", f"{selected_row['CDI Acumulado (%)']:.2f}%")
                st.metric("Performance vs CDI", f"{selected_row['Performance vs CDI (%)']:.2f}%")

            tab1, tab2 = st.tabs(["📊 Histórico", "💵 Dividendos"])

            with tab1:
                st.write("Histórico completo de preços")
                st.area_chart(historicos[ticker]['Close'].rename('Preço (R$)'))
                st.write("Últimos pregões:")
                st.dataframe(
                    historicos[ticker][['Open', 'High', 'Low', 'Close', 'Volume']].tail(10).style.format('R${:,.2f}'),
                    use_container_width=True
                )

            with tab2:
                st.write("Histórico de dividendos (últimos 12 meses)")
                dividendos_df = get_dividendos_12m(ticker)
                if dividendos_df is not None and not dividendos_df.empty:
                    st.dataframe(
                        dividendos_df.reset_index().rename(columns={'Date': 'Data', 'Dividends': 'Valor'}),
                        column_config={
                            "Data": st.column_config.DateColumn("Data"),
                            "Valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f")
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                else:
                    st.info("Nenhum dividendo pago nos últimos 12 meses")

    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
    finally:
        session.remove()
