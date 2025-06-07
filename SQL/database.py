# SQL/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from .models import Base
import os
from threading import Lock

_engine = None
_session_factory = None
_lock = Lock()
_db_initialized = False  # Variável de controle

def init_db():
    global _engine, _session_factory, _db_initialized
    
    with _lock:
        if _engine is None:
            os.makedirs("data", exist_ok=True)
            db_path = 'sqlite:///data/ativos.db'
            _engine = create_engine(db_path, connect_args={"check_same_thread": False})
            
            # Verifica se o banco já existe
            db_exists = os.path.exists("data/ativos.db")
            
            if not db_exists:
                Base.metadata.create_all(_engine)
                _db_initialized = True
            else:
                # Se o banco existe, apenas conecta sem recriar
                _db_initialized = True

            _session_factory = sessionmaker(bind=_engine)

def get_db_session():
    init_db()
    return scoped_session(_session_factory)