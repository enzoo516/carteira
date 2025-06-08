# frontend/main.py (se você manteve sua estrutura de navegação original)
import streamlit as st
from modules import ativos
from modules import operacoes
from modules import informacoes

st.set_page_config(
    page_title="Gestão de Investimentos",
    layout="wide",
    menu_items={ 'Get Help': None, 'Report a bug': None, 'About': None }
)

hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

with st.sidebar:
    st.title("Menu de Navegação")
    pagina = st.radio(
        "Selecione o módulo:",
        options=["Ativos", "Operações", "Informações"],
        label_visibility="collapsed"
    )

if pagina == "Ativos":
    ativos.show_ativos()
elif pagina == "Operações":
    operacoes.show_operacoes()
elif pagina == "Informações":
    informacoes.show_informacoes()
