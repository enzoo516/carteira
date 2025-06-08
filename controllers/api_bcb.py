# controllers/api_bcb.py
from datetime import datetime
from dateutil.relativedelta import relativedelta
import requests

def get_cdi_accumulated():
    """Obtém o CDI acumulado dos últimos 12 meses do Banco Central"""
    end_date = datetime.now()
    start_date = end_date - relativedelta(years=1)
    
    url = (
        f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados"
        f"?formato=json&dataInicial={start_date.strftime('%d/%m/%Y')}"
        f"&dataFinal={end_date.strftime('%d/%m/%Y')}"
    )
    
    try:
        response = requests.get(url)
        data = response.json()
        
        acumulado = 1.0
        for entry in data:
            acumulado *= (1 + float(entry['valor']) / 100)
        
        return (acumulado - 1) * 100  # Retorna em porcentagem
    
    except Exception:
        return 8.5  # Fallback
