# frontend/pages/informacoes.py
import streamlit as st
import pandas as pd
import requests

API_URL = "http://127.0.0.1:8000"

def show_informacoes():
    st.title("📊 Informações e Desempenho dos Ativos")

    # A complexidade toda foi substituída por uma única chamada de API
    with st.spinner("Buscando e calculando dados da carteira..."):
        try:
            response = requests.get(f"{API_URL}/api/dashboard/performance")
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Erro de conexão: Não foi possível obter os dados do dashboard. {e}")
            return

    df_ativos = pd.DataFrame(data.get("ativos", []))
    metricas = data.get("metricas_gerais", {})
    historicos = data.get("historicos", {})
    cdi_acumulado = data.get("cdi", 0.0)

    if df_ativos.empty:
        st.warning("Nenhum dado de ativo para exibir. Cadastre ativos e operações primeiro.")
        return

    df_ativos['Performance vs CDI (%)'] = df_ativos['Rendimento Total (%)'] - cdi_acumulado

    # O resto do código é apenas para exibir os dados já processados
    st.subheader("📈 Desempenho Geral da Carteira")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Investido", f"R$ {metricas.get('total_investido', 0):,.2f}")
    col2.metric("Valor Atual", f"R$ {metricas.get('valor_atual', 0):,.2f}", f"{metricas.get('rendimento_total_percent', 0):.2f}%")
    col3.metric("Rendimento Total", f"{metricas.get('rendimento_total_percent', 0):.2f}%")
    col4.metric("Dividendos Recebidos", f"R$ {metricas.get('dividendos_total', 0):,.2f}")

    st.subheader("📋 Resumo por Ativo")
    st.dataframe(df_ativos.style.format({
        'Preço Atual': 'R${:,.2f}', 'Total Investido': 'R${:,.2f}',
        'Valor Atual': 'R${:,.2f}', 'Rendimento Total (%)': '{:.2f}%',
        'Dividendos': 'R${:,.2f}', 'Performance vs CDI (%)': '{:.2f}%'
    }), use_container_width=True, hide_index=True)
    
    # Detalhes do ativo selecionado
    if not df_ativos.empty:
        st.subheader(f"📌 Detalhes do Ativo")
        ticker = st.selectbox("Selecione um Ativo", options=df_ativos['Ticker'])
        
        # O histórico agora vem do payload da API
        if ticker and ticker in historicos:
            historico_df = pd.read_json(historicos[ticker], orient='split')
            st.line_chart(historico_df['Close'].rename('Preço (R$)'))

        # A busca de dividendos também é uma chamada de API
        if ticker:
            try:
                div_response = requests.get(f"{API_URL}/api/dividendos/{ticker}")
                div_response.raise_for_status()
                dividendos_df = pd.DataFrame(div_response.json())
                if not dividendos_df.empty:
                    st.write("Dividendos (últimos 12 meses)")
                    st.dataframe(dividendos_df, hide_index=True, use_container_width=True)
                else:
                    st.info("Nenhum dividendo pago nos últimos 12 meses para este ativo.")
            except requests.exceptions.RequestException:
                st.error(f"Não foi possível buscar os dividendos para {ticker}.")

