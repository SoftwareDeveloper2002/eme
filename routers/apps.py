from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import App
from docker_manager import deploy_container
import random

router = APIRouter()

@router.post("/deploy")
def deploy_app(app_name: str, db: Session = Depends(get_db)):

    port = random.randint(9000, 9999)
    container_name = f"{app_name}-{port}"

    container_id = deploy_container(
        image_name="nginx",
        container_name=container_name,
        port=port
    )

    app = App(name=app_name, container_id=container_id, port=port)
    db.add(app)
    db.commit()

    return {
        "message": "App deployed",
        "container_id": container_id,
        "port": port
    }