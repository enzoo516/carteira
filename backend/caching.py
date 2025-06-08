# backend/caching.py
import functools
from cachetools import TTLCache

# Cria um cache que guarda no máximo 512 itens e cada item "vive" por um tempo específico (TTL).
# Usaremos um cache diferente para cada tipo de dado.
# Cache para dados que mudam com frequência (cotações): 15 minutos (900 segundos)
market_data_cache = TTLCache(maxsize=512, ttl=900)

# Cache para dados que mudam raramente (CDI): 4 horas (14400 segundos)
infrequent_data_cache = TTLCache(maxsize=128, ttl=14400)


def cached(cache):
    """
    Decorator que aplica um cache específico a uma função.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Cria uma chave única baseada no nome da função e seus argumentos
            key = functools._make_key(args, kwargs, typed=False)

            # Tenta pegar o resultado do cache
            try:
                result = cache[key]
                # print(f"HIT: Servindo do cache para a chave: {key}") # Descomente para debug
                return result
            except KeyError:
                # Se não encontrar, executa a função original
                # print(f"MISS: Executando função e salvando no cache para a chave: {key}") # Descomente para debug
                result = func(*args, **kwargs)
                # Salva o novo resultado no cache
                cache[key] = result
                return result

        return wrapper

    return decorator