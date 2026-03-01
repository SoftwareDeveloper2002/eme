from fastapi import FastAPI
from routers.apps import router as apps_router

app = FastAPI()

app.include_router(apps_router)

@app.get("/")
def root():
    return {"message": "Backend running"}