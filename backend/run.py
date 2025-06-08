import uvicorn

if __name__ == "__main__":
    """
    Este é o ponto de entrada principal para iniciar o servidor de backend.

    Ele executa o servidor Uvicorn programaticamente, o que é uma alternativa
    conveniente a rodar o comando diretamente no terminal.

    Rodar este arquivo com 'python run.py' é equivalente a executar:
    'uvicorn api:app --host 127.0.0.1 --port 8000 --reload'
    """
    uvicorn.run(
        "api:app",          # A referência para a sua aplicação FastAPI: 'nome_do_arquivo:nome_da_variavel_app'
        host="127.0.0.1",   # O endereço de host para o servidor
        port=8000,          # A porta em que o servidor irá escutar
        reload=True         # Habilita o auto-reload, que reinicia o servidor automaticamente após mudanças no código
    )
