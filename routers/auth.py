from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User
from pydantic import BaseModel
import bcrypt

router = APIRouter()

class UserRegister(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str


@router.post("/register")
def register(data: UserRegister, db: Session = Depends(get_db)):

    # check if user already exists
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()

    user = User(email=data.email, password=hashed)
    db.add(user)
    db.commit()

    return {"message": "registered"}


@router.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")

    if not bcrypt.checkpw(data.password.encode(), user.password.encode()):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    return {
        "message": "login successful",
        "user_id": user.id,
        "email": user.email
    }