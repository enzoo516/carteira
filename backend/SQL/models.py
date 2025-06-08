# SQL/models.py
from sqlalchemy import Column, Integer, String, Date, Numeric, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Ativo(Base):
    __tablename__ = 'ativos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), unique=True, nullable=False)
    tipo_ativo = Column(String(4), nullable=False)  # 'FII', 'ETF' ou 'Ação'

    operacoes = relationship("Operacao", back_populates="ativo")

class Operacao(Base):
    __tablename__ = 'operacoes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_ticker = Column(Integer, ForeignKey('ativos.id'), nullable=False)  # Relacionamento com a tabela ativos
    tipo_operacao = Column(String(7), nullable=False)  # 'Comprar' ou 'Vender'
    data_operacao = Column(Date, nullable=False)
    preco = Column(Numeric(10, 2), nullable=False)
    quantidade = Column(Integer, nullable=False)

    ativo = relationship("Ativo", back_populates="operacoes")