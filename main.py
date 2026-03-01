from fastapi import FastAPI
from routers import apps
from routers.auth import router as auth_router  
from database import Base, engine
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
Base.metadata.create_all(bind=engine)
app.include_router(auth_router, prefix="/auth")
app.include_router(apps.router)

@app.get("/")
def root():
    return {"message": "Backend running....."}