from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from database import get_db
from docker_manager import deploy_container
from models import App
import random
import json

router = APIRouter()

@router.post("/deploy")
async def deploy_webhook(request: Request, db: Session = Depends(get_db)):

    payload = await request.json()

    repo = payload["repository"]["name"]
    branch = payload["ref"]

    # Only deploy main branch
    if branch != "refs/heads/main":
        return {"message": "ignored"}

    port = random.randint(9000, 9999)
    container_name = f"{repo}-{port}"

    container_id = deploy_container(
        image_name=repo,
        container_name=container_name,
        port=port
    )

    app = App(name=repo, container_id=container_id, port=port)
    db.add(app)
    db.commit()

    return {
        "message": "deployed",
        "container_id": container_id,
        "port": port
    }