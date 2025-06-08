# controllers/yahoo_finance.py
import yfinance as yf

def get_ativo_info(ticker):
    """Obtém informações de preço, histórico e dividendos do ativo"""
    try:
        ticker_adjusted = f"{ticker}.SA"
        ativo = yf.Ticker(ticker_adjusted)
        hist = ativo.history(period="1y")
        
        if hist.empty:
            return None
        
        preco_atual = hist['Close'].iloc[-1]
        preco_6m = hist['Close'].iloc[0] if len(hist) > 0 else preco_atual
        preco_1m = hist['Close'].iloc[-20] if len(hist) > 20 else preco_atual
        preco_ontem = hist['Close'].iloc[-2] if len(hist) > 1 else preco_atual
        
        rendimento_6m = ((preco_atual - preco_6m) / preco_6m) * 100
        rendimento_1m = ((preco_atual - preco_1m) / preco_1m) * 100
        rendimento_dia = ((preco_atual - preco_ontem) / preco_ontem) * 100
        
        dividendos = ativo.dividends.last('1Y').sum()
        
        return {
            'Preço Atual': preco_atual,
            'Rendimento 6M (%)': rendimento_6m,
            'Rendimento Mês (%)': rendimento_1m,
            'Rendimento Dia (%)': rendimento_dia,
            'Dividendos 12M': dividendos,
            'Histórico': hist
        }

    except Exception:
        return None


def get_dividendos_12m(ticker):
    """Obtém DataFrame de dividendos pagos nos últimos 12 meses"""
    try:
        ativo = yf.Ticker(f"{ticker}.SA")
        dividendos = ativo.dividends.last("1Y")
        return dividendos
    except Exception:
        return None
