# migrate.py
from SQL.database import init_db, get_db_session
from SQL.models import Operacao

def migrate_database():
    session = get_db_session()
    try:
        # Para versões anteriores que usavam 'ativo_id' em vez de 'id_ticker'
        operacoes = session.query(Operacao).all()
        for op in operacoes:
            if hasattr(op, 'ativo_id') and not hasattr(op, 'id_ticker'):
                op.id_ticker = op.ativo_id
        session.commit()
        print("Migração concluída com sucesso!")
    except Exception as e:
        session.rollback()
        print(f"Erro na migração: {e}")
    finally:
        session.remove()

if __name__ == "__main__":
    init_db()
    migrate_database()