# backend/controllers/api_bcb.py
from datetime import datetime
from dateutil.relativedelta import relativedelta
import requests
from backend.caching import cached, infrequent_data_cache  # Importa o decorator e o cache específico


@cached(infrequent_data_cache)
def get_cdi_accumulated():
    """Obtém o CDI acumulado dos últimos 12 meses do Banco Central. O resultado é cacheado."""
    end_date = datetime.now()
    start_date = end_date - relativedelta(years=1)

    url = (
        f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados"
        f"?formato=json&dataInicial={start_date.strftime('%d/%m/%Y')}"
        f"&dataFinal={end_date.strftime('%d/%m/%Y')}"
    )

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data:
            return 0.0

        acumulado = 1.0
        for entry in data:
            acumulado *= (1 + float(entry['valor']) / 100)

        return (acumulado - 1) * 100
    except Exception:
        return None
