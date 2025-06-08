# backend/api.py

from fastapi import FastAPI, APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List
from datetime import date
import pandas as pd

# Imports da lógica existente, com os caminhos relativos corretos
from SQL import models, database
# O arquivo de backup não é chamado pela API diretamente, mas pode ser mantido para scripts manuais
# A lógica de utilities foi removida conforme solicitado
from controllers import yahoo_finance, api_bcb
from pydantic import BaseModel

# Inicializa o banco de dados na inicialização da API
database.init_db()

# --- Modelos Pydantic (Definem o formato dos dados da API) ---
class AtivoBase(BaseModel):
    ticker: str
    tipo_ativo: str

class Ativo(AtivoBase):
    id: int
    class Config:
        orm_mode = True

class OperacaoBase(BaseModel):
    id_ticker: int
    tipo_operacao: str
    data_operacao: date
    preco: float
    quantidade: int

class Operacao(OperacaoBase):
    id: int
    class Config:
        orm_mode = True

# --- Configuração da Aplicação Principal ---
app = FastAPI(
    title="API da Carteira de Investimentos",
    description="Backend para a aplicação de gestão de portfólio.",
    version="1.0.0"
)

# --- Dependência para obter a sessão do banco ---
def get_db():
    db = database.get_db_session()
    try:
        yield db
    finally:
        db.remove()

# --- Roteadores para organizar os endpoints ---
router_ativos = APIRouter(prefix="/api/ativos", tags=["Ativos"])
router_operacoes = APIRouter(prefix="/api/operacoes", tags=["Operações"])
router_dashboard = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])
router_market_data = APIRouter(prefix="/api/market-data", tags=["Dados de Mercado Externo"])


# =================================================================
# === ENDPOINTS PARA ATIVOS =======================================
# =================================================================
@router_ativos.get("/", response_model=List[Ativo])
def listar_ativos(db: Session = Depends(get_db)):
    return db.query(models.Ativo).order_by(models.Ativo.ticker).all()

@router_ativos.post("/", response_model=Ativo, status_code=201)
def criar_ativo(ativo: AtivoBase, db: Session = Depends(get_db)):
    if db.query(models.Ativo).filter(models.Ativo.ticker == ativo.ticker).first():
        raise HTTPException(status_code=400, detail="Este ticker já está cadastrado!")
    novo_ativo = models.Ativo(**ativo.dict())
    db.add(novo_ativo)
    db.commit()
    db.refresh(novo_ativo)
    return novo_ativo

@router_ativos.post("/delete")
def deletar_ativos(ids: List[int] = Body(..., embed=True), db: Session = Depends(get_db)):
    if not ids:
        raise HTTPException(status_code=400, detail="Nenhuma ID fornecida.")
    query = db.query(models.Ativo).filter(models.Ativo.id.in_(ids))
    deleted_count = query.delete(synchronize_session=False)
    db.commit()
    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="Nenhum ativo encontrado com os IDs fornecidos.")
    return {"detail": f"{deleted_count} ativo(s) excluído(s) com sucesso!"}

# =================================================================
# === ENDPOINTS PARA OPERAÇÕES ====================================
# =================================================================
@router_operacoes.get("/")
def listar_operacoes(data_inicio: date, data_fim: date, db: Session = Depends(get_db)):
    operacoes = db.query(models.Operacao, models.Ativo) \
        .join(models.Ativo, models.Operacao.id_ticker == models.Ativo.id) \
        .filter(models.Operacao.data_operacao.between(data_inicio, data_fim)) \
        .order_by(models.Operacao.data_operacao.desc()).all()
    resultado = [{
        "id": op.id, "ticker": ativo.ticker, "tipo_ativo": ativo.tipo_ativo,
        "tipo_operacao": op.tipo_operacao, "data_operacao": op.data_operacao,
        "preco": float(op.preco), "quantidade": op.quantidade
    } for op, ativo in operacoes]
    return resultado

@router_operacoes.get("/{operacao_id}")
def obter_operacao(operacao_id: int, db: Session = Depends(get_db)):
    op_info = db.query(models.Operacao, models.Ativo).join(models.Ativo).filter(models.Operacao.id == operacao_id).first()
    if not op_info:
        raise HTTPException(status_code=404, detail="Operação não encontrada")
    op, ativo = op_info
    return { "id": op.id, "id_ticker": op.id_ticker, "ticker": ativo.ticker, "tipo_operacao": op.tipo_operacao, "data_operacao": op.data_operacao, "preco": float(op.preco), "quantidade": op.quantidade }

@router_operacoes.post("/", response_model=Operacao, status_code=201)
def criar_operacao(operacao: OperacaoBase, db: Session = Depends(get_db)):
    nova_operacao = models.Operacao(**operacao.dict())
    db.add(nova_operacao)
    db.commit()
    db.refresh(nova_operacao)
    return nova_operacao

@router_operacoes.put("/{operacao_id}", response_model=Operacao)
def atualizar_operacao(operacao_id: int, dados: OperacaoBase, db: Session = Depends(get_db)):
    db_operacao = db.query(models.Operacao).filter(models.Operacao.id == operacao_id).first()
    if not db_operacao:
        raise HTTPException(status_code=404, detail="Operação não encontrada")
    for key, value in dados.dict().items():
        setattr(db_operacao, key, value)
    db.commit()
    db.refresh(db_operacao)
    return db_operacao

@router_operacoes.post("/delete")
def deletar_operacoes(ids: List[int] = Body(..., embed=True), db: Session = Depends(get_db)):
    deleted_count = db.query(models.Operacao).filter(models.Operacao.id.in_(ids)).delete(synchronize_session=False)
    db.commit()
    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="Nenhuma operação encontrada.")
    return {"detail": f"{deleted_count} operação(ões) excluída(s) com sucesso!"}

# =================================================================
# === ENDPOINTS PARA DASHBOARD DE PERFORMANCE =====================
# =================================================================
@router_dashboard.get("/performance")
def get_performance_carteira(db: Session = Depends(get_db)):
    ativos_db = db.query(models.Ativo).all()
    if not ativos_db:
        return {"ativos": [], "metricas_gerais": {}, "cdi": 0, "historicos": {}}

    cdi_acumulado = api_bcb.get_cdi_accumulated()
    dados_ativos = []
    historicos_para_frontend = {}

    for ativo in ativos_db:
        operacoes = db.query(models.Operacao).filter(models.Operacao.id_ticker == ativo.id).all()
        if not operacoes: continue

        total_investido = sum(float(op.preco) * op.quantidade for op in operacoes if op.tipo_operacao == 'Comprar')
        total_vendido = sum(float(op.preco) * op.quantidade for op in operacoes if op.tipo_operacao == 'Vender')
        quantidade_atual = sum(op.quantidade for op in operacoes if op.tipo_operacao == 'Comprar') - sum(op.quantidade for op in operacoes if op.tipo_operacao == 'Vender')
        
        info_yh = yahoo_finance.get_ativo_info(ativo.ticker)
        if info_yh:
            preco_atual = info_yh.get('Preço Atual', 0)
            valor_atual_ativo = quantidade_atual * preco_atual
            rendimento_total = ((valor_atual_ativo + total_vendido) - total_investido) / total_investido * 100 if total_investido > 0 else 0
            
            dados_ativos.append({
                'Ticker': ativo.ticker, 'Tipo': ativo.tipo_ativo, 'Preço Atual': preco_atual,
                'Total Investido': total_investido, 'Valor Atual': valor_atual_ativo,
                'Rendimento Total (%)': rendimento_total, 'Dividendos': info_yh.get('Dividendos 12M', 0),
            })
            historicos_para_frontend[ativo.ticker] = info_yh['Histórico'].to_json(orient='split')

    if not dados_ativos:
         return {"ativos": [], "metricas_gerais": {}, "cdi": cdi_acumulado, "historicos": {}}
    
    df_ativos = pd.DataFrame(dados_ativos)
    total_investido_carteira = df_ativos['Total Investido'].sum()
    valor_atual_carteira = df_ativos['Valor Atual'].sum()
    rend_total_carteira = ((valor_atual_carteira - total_investido_carteira) / total_investido_carteira) * 100 if total_investido_carteira > 0 else 0
    dividendos_carteira = df_ativos['Dividendos'].sum()

    return {
        "ativos": df_ativos.to_dict(orient='records'),
        "metricas_gerais": { "total_investido": total_investido_carteira, "valor_atual": valor_atual_carteira, "rendimento_total_percent": rend_total_carteira, "dividendos_total": dividendos_carteira },
        "historicos": historicos_para_frontend, "cdi": cdi_acumulado
    }

# =================================================================
# === ENDPOINTS DE DADOS DE MERCADO (BCB, Yahoo Finance) ==========
# =================================================================

@router_market_data.get("/cdi")
def get_cdi():
    cdi = api_bcb.get_cdi_accumulated()
    if cdi is None:
        raise HTTPException(status_code=500, detail="Não foi possível buscar os dados do CDI.")
    return {"cdi_acumulado_12m": cdi}

@router_market_data.get("/ativo/{ticker}/info")
def get_info_ativo(ticker: str):
    info = yahoo_finance.get_ativo_info(ticker)
    if info is None:
        raise HTTPException(status_code=404, detail=f"Não foram encontradas informações para o ticker {ticker}.")
    info['Histórico'] = info['Histórico'].to_json(orient='split')
    return info

@router_market_data.get("/ativo/{ticker}/dividendos")
def get_dividendos(ticker: str):
    dividendos_df = yahoo_finance.get_dividendos_12m(ticker)
    if dividendos_df is None: return []
    dividendos_df = dividendos_df.reset_index()
    dividendos_df.columns = ['Data', 'Valor']
    return dividendos_df.to_dict(orient='records')


# --- Inclui todos os roteadores na aplicação principal ---
app.include_router(router_ativos)
app.include_router(router_operacoes)
app.include_router(router_dashboard)
app.include_router(router_market_data)