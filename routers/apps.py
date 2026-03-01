from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from docker_manager import deploy_container
from models import App, User
import random
import subprocess
import os
import shutil
import requests

router = APIRouter()

GITHUB_CLIENT_ID = " Ov23livvFJQfqDGKUVno"
GITHUB_CLIENT_SECRET = "1cc551b1f1a4d153ece8d79bddf147fd2348f05a"

# ====== GitHub OAuth Login ======
@router.get("/github/login")
def github_login():
    return {
        "url": (
            "https://github.com/login/oauth/authorize"
            f"?client_id={GITHUB_CLIENT_ID}"
            "&scope=repo"
        )
    }

@router.get("/github/callback")
def github_callback(code: str, db: Session = Depends(get_db)):
    # Exchange code for token
    res = requests.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data={
            "client_id": GITHUB_CLIENT_ID,
            "client_secret": GITHUB_CLIENT_SECRET,
            "code": code
        }
    )

    token = res.json().get("access_token")
    if not token:
        raise HTTPException(status_code=400, detail="OAuth failed")

    return {"access_token": token}


# ====== List Repositories ======
@router.get("/github/repos")
def list_repos(token: str):
    headers = {"Authorization": f"token {token}"}
    repos = requests.get("https://api.github.com/user/repos", headers=headers).json()
    return repos


# ====== Deploy Selected Repo ======
class DeployRequest:
    repo_name: str
    token: str

@router.post("/deploy")
async def deploy_repo(data: DeployRequest, db: Session = Depends(get_db)):

    headers = {"Authorization": f"token {data.token}"}
    repo = requests.get(
        f"https://api.github.com/repos/{data.repo_name}",
        headers=headers
    ).json()

    clone_url = repo.get("clone_url")
    if not clone_url:
        raise HTTPException(status_code=400, detail="Repo not accessible")

    workdir = f"/tmp/{data.repo_name}"

    if os.path.exists(workdir):
        shutil.rmtree(workdir)

    try:
        subprocess.run(["git", "clone", clone_url, workdir], check=True)
        subprocess.run(["docker", "build", "-t", data.repo_name, workdir], check=True)

        port = random.randint(9000, 9999)
        container_name = f"{data.repo_name}-{port}"

        container_id = deploy_container(
            image_name=data.repo_name,
            container_name=container_name,
            port=port
        )

        app = App(name=data.repo_name, container_id=container_id, port=port)
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