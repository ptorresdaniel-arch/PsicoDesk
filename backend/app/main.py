from fastapi import FastAPI

from app.users.router import router as users_router


app = FastAPI(
    title="PsicoDesk API",
    version="0.1.0",
)


app.include_router(users_router)


@app.get("/")
def root():
    return {"message": "PsicoDesk API funcionando!"}