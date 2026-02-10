from fastapi import FastAPI

app = FastAPI()


@app.get("/dados")
def obter_dados(numero: int):
    return {
        "numero": numero,
        "status": "ok",
        "descricao": "dado ficticio"
    }
