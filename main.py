from fastapi import FastAPI
from routers import apps

app = FastAPI()

app.include_router(apps.router)

@app.get("/")
def root():
    return {"message": "Backend running"}