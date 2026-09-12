from fastapi import FastAPI

app = FastAPI(
    title="PsicoDesk API",
    version="0.1.0"
)

@app.get("/")
def root():
    return {"message": "PsicoDesk API funcionando!"}