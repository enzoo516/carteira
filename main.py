# main.py
import streamlit as st
from SQL.database import init_db
from pages import utilities

# Inicializa o banco de dados apenas uma vez
if 'db_initialized' not in st.session_state:
    init_db()
    st.session_state.db_initialized = True

# Configuração da página
st.set_page_config(page_title="Gestão de Investimentos", layout="wide")

# Barra lateral para navegação
st.sidebar.title("Menu")
pagina = st.sidebar.radio("Selecione o módulo:", ["Ativos", "Operações"])

# Navegação entre páginas
if pagina == "Ativos":
    from pages import ativos
    ativos.show_ativos()
elif pagina == "Operações":
    from pages import operacoes
    operacoes.show_operacoes()

elif pagina == "Utilidades":
    from pages import utilities
    if st.button("Popular com dados de exemplo"):
        utilities.popular_dados_exemplo()