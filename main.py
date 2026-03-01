from fastapi import FastAPI
from routers import apps
from auth import router as auth_router
from database import Base, engine

app = FastAPI()

# Create tables
Base.metadata.create_all(bind=engine)
app.include_router(auth_router)
app.include_router(apps.router)

@app.get("/")
def root():
    return {"message": "Backend running....."}