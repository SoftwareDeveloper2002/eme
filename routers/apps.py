from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from docker_manager import deploy_container
from models import App
import random
import subprocess
import os
import shutil

router = APIRouter()

@router.post("/deploy")
async def deploy_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Validate payload
    repository = payload.get("repository")
    if not repository:
        raise HTTPException(status_code=400, detail="No repository data")

    repo_name = repository.get("name")
    repo_url = repository.get("clone_url")
    ref = payload.get("ref")

    if not repo_name or not repo_url or not ref:
        raise HTTPException(status_code=400, detail="Missing repository info")

    # Only deploy main branch
    if ref != "refs/heads/main":
        return {"message": "ignored"}

    workdir = f"/tmp/{repo_name}"

    # Clean previous clone
    if os.path.exists(workdir):
        shutil.rmtree(workdir)

    try:
        # Clone repo
        subprocess.run(["git", "clone", repo_url, workdir], check=True)

        # Build Docker image
        subprocess.run(["docker", "build", "-t", repo_name, workdir], check=True)

        # Deploy container
        port = random.randint(9000, 9999)
        container_name = f"{repo_name}-{port}"

        container_id = deploy_container(
            image_name=repo_name,
            container_name=container_name,
            port=port
        )

        # Save deployment record
        app = App(name=repo_name, container_id=container_id, port=port)
        db.add(app)
        db.commit()

        return {
            "message": "deployed",
            "container_id": container_id,
            "port": port
        }

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Build error: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deployment error: {str(e)}")