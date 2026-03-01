from fastapi import FastAPI
from routers import apps
from routers.auth import router as auth_router  # FIXED
from database import Base, engine

app = FastAPI()

Base.metadata.create_all(bind=engine)
app.include_router(auth_router, prefix="/auth")
app.include_router(apps.router)

@app.get("/")
def root():
    return {"message": "Backend running....."}