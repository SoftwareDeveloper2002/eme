from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User
from pydantic import BaseModel
import bcrypt

router = APIRouter()

class UserRegister(BaseModel):
    email: str
    password: str

@router.post("/register")
def register(data: UserRegister, db: Session = Depends(get_db)):
    hashed = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()

    user = User(email=data.email, password=hashed)
    db.add(user)
    db.commit()

    return {"message": "registered"}