from fastapi import FastAPI
from routers import apps
from database import Base, engine

app = FastAPI()

# Create tables
Base.metadata.create_all(bind=engine)

app.include_router(apps.router)

@app.get("/")
def root():
    return {"message": "Backend running"}