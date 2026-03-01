from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)

    apps = relationship("App", back_populates="owner")


class App(Base):
    __tablename__ = "apps"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    container_id = Column(String)
    port = Column(Integer)

    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="apps")