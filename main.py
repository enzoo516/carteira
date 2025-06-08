# main.py atualizado
import streamlit as st
from SQL.database import init_db

# Configurações da página
st.set_page_config(
    page_title="Gestão de Investimentos",
    layout="wide",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Esconde o menu padrão do Streamlit
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Inicialização do banco
if 'db_initialized' not in st.session_state:
    init_db()
    st.session_state.db_initialized = True

# Barra lateral de navegação
with st.sidebar:
    st.title("Menu de Navegação")
    pagina = st.radio(
        "Selecione o módulo:",
        options=["Ativos", "Operações", "Informações", "Utilitários"],
        label_visibility="collapsed"
    )

# Navegação entre páginas
if pagina == "Ativos":
    from pages import ativos
    ativos.show_ativos()
elif pagina == "Operações":
    from pages import operacoes
    operacoes.show_operacoes()
elif pagina == "Informações":
    from pages import informacoes
    informacoes.show_informacoes()
