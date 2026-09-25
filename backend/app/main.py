from fastapi import FastAPI

from app.users.router import router as users_router
from app.auth.router import router as auth_router
from app.patients.router import router as patients_router
from app.clinical_sessions.router import router as clinical_sessions_router
from app.appointments.router import router as appointments_router

app = FastAPI(
    title="PsicoDesk API",
    version="0.1.0",
    description=(
        "API para la gestión de pacientes, agenda "
        "y atención clínica psicológica."
    )
)


app.include_router(users_router)
app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(clinical_sessions_router)
app.include_router(appointments_router)


@app.get("/")
def root():
    return {"message": "PsicoDesk API funcionando!"}