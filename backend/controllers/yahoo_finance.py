# backend/controllers/yahoo_finance.py
import yfinance as yf
from backend.caching import cached, market_data_cache  # Importa o decorator e o cache específico


@cached(market_data_cache)
def get_ativo_info(ticker: str):
    """Obtém informações de preço, histórico e dividendos do ativo. O resultado é cacheado."""
    try:
        if not ticker.endswith('.SA'):
            ticker_adjusted = f"{ticker}.SA"
        else:
            ticker_adjusted = ticker

        ativo = yf.Ticker(ticker_adjusted)
        inf = ativo.info
        hist = ativo.history(period="1y")


        if hist.empty:
            return None

        preco_atual = hist['Close'].iloc[-1]
        preco_ontem = hist['Close'].iloc[-2] if len(hist) > 1 else preco_atual
        dividendos = ativo.dividends.last('365d').sum()

        return {
            'Preço Atual': preco_atual,
            'Rendimento Dia (%)': ((preco_atual - preco_ontem) / preco_ontem) * 100 if preco_ontem != 0 else 0,
            'Dividendos 12M': dividendos,
            'Histórico': hist
        }
    except Exception as e:
        print(f"Erro ao carregar os dados do ticker {ticker}: {e}")


@cached(market_data_cache)
def get_dividendos_12m(ticker: str):
    """Obtém DataFrame de dividendos pagos nos últimos 12 meses. O resultado é cacheado."""
    try:
        if not ticker.endswith('.SA'):
            ticker_adjusted = f"{ticker}.SA"
        else:
            ticker_adjusted = ticker

        ativo = yf.Ticker(ticker_adjusted)
        dividendos = ativo.dividends.last("365d")
        return dividendos
    except Exception:
        return None
