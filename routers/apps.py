from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from docker_manager import deploy_container
from models import App
import subprocess

router = APIRouter()

@router.post("/deploy")
async def deploy_webhook(request: Request, db: Session = Depends(get_db)):

    payload = await request.json()

    # GitHub push event validation
    repo = payload.get("repository", {}).get("name")
    ref = payload.get("ref")

    if not repo or not ref:
        raise HTTPException(status_code=400, detail="invalid payload")

    # Only deploy main branch
    if ref != "refs/heads/main":
        return {"message": "ignored"}

    # Pull latest code
    subprocess.run(["git", "pull", "origin", "main"], check=True)

    # Build Docker image from repo
    subprocess.run(["docker", "build", "-t", repo, "."], check=True)

    # Deploy container
    port = 9000
    container_name = f"{repo}-latest"

    container_id = deploy_container(
        image_name=repo,
        container_name=container_name,
        port=port
    )

    # Save DB record
    app = App(name=repo, container_id=container_id, port=port)
    db.add(app)
    db.commit()

    return {
        "message": "deployed",
        "container_id": container_id,
        "port": port
    }