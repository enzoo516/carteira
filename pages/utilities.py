# pages/utilities.py (crie este novo arquivo)
from SQL.database import get_db_session
from SQL.models import Ativo, Operacao
from datetime import date, timedelta
import random

def popular_dados_exemplo():
    session = get_db_session()
    try:
        # Limpa tabelas existentes (opcional)
        session.query(Operacao).delete()
        session.query(Ativo).delete()
        
        # Cria ativos de exemplo
        ativos = [
            Ativo(ticker="XPML11", tipo_ativo="FII"),
            Ativo(ticker="BOVA11", tipo_ativo="ETF"),
            Ativo(ticker="PETR4", tipo_ativo="Ação"),
            Ativo(ticker="VALE3", tipo_ativo="Ação"),
            Ativo(ticker="MXRF11", tipo_ativo="FII")
        ]
        session.add_all(ativos)
        session.commit()
        
        # Cria operações de exemplo
        tipos = ['Comprar', 'Vender']
        for i in range(1, 6):
            for _ in range(3):  # 3 operações por ativo
                operacao = Operacao(
                    id_ticker=i,
                    tipo_operacao=random.choice(tipos),
                    data_operacao=date.today() - timedelta(days=random.randint(0, 30)),
                    preco=round(random.uniform(10, 150), 2),
                    quantidade=random.randint(1, 100)
                )
                session.add(operacao)
        session.commit()
        st.success("✅ Dados de exemplo criados com sucesso!")
    except Exception as e:
        session.rollback()
        st.error(f"Erro ao criar dados: {e}")
    finally:
        session.remove()