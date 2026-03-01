from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from docker_manager import deploy_container
from models import App
import random
import subprocess
import os
import shutil
import requests

router = APIRouter()

# GitHub OAuth credentials
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
    raise RuntimeError("GitHub OAuth environment variables not set")


# ---------------------------
# GitHub OAuth Login
# ---------------------------

@router.get("/github/login")
def github_login():
    return {
        "url": (
            "https://github.com/login/oauth/authorize"
            f"?client_id={GITHUB_CLIENT_ID}"
            "&scope=repo"
        )
    }


# ---------------------------
# GitHub OAuth Callback
# ---------------------------

@router.get("/github/callback")
def github_callback(code: str, db: Session = Depends(get_db)):
    res = requests.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data={
            "client_id": GITHUB_CLIENT_ID,
            "client_secret": GITHUB_CLIENT_SECRET,
            "code": code
        }
    )

    data = res.json()
    token = data.get("access_token")

    if not token:
        raise HTTPException(status_code=400, detail="OAuth failed")

    # Redirect back to frontend with token (frontend will store it)
    frontend_url = "https://cloudhosting.soltryxsolutions.com/dashboard"

    return RedirectResponse(
        url=f"{frontend_url}?token={token}"
    )


# ---------------------------
# GitHub Repositories
# ---------------------------

@router.get("/github/repos")
def list_repos(token: str):
    headers = {"Authorization": f"token {token}"}
    res = requests.get("https://api.github.com/user/repos", headers=headers)

    if res.status_code != 200:
        raise HTTPException(status_code=400, detail="Invalid token")

    return res.json()


# ---------------------------
# Deploy Request Model
# ---------------------------

class DeployRequest(BaseModel):
    repo_name: str
    token: str


# ---------------------------
# Deploy Endpoint
# ---------------------------

@router.post("/deploy")
async def deploy_repo(data: DeployRequest, db: Session = Depends(get_db)):

    headers = {"Authorization": f"token {data.token}"}

    repo_res = requests.get(
        f"https://api.github.com/repos/{data.repo_name}",
        headers=headers
    )

    if repo_res.status_code != 200:
        raise HTTPException(status_code=400, detail="Repo not accessible")

    repo = repo_res.json()
    clone_url = repo.get("clone_url")

    if not clone_url:
        raise HTTPException(status_code=400, detail="Invalid repository")

    workdir = f"/tmp/{data.repo_name.replace('/', '_')}"

    if os.path.exists(workdir):
        shutil.rmtree(workdir)

    try:
        # Clone repository
        subprocess.run(["git", "clone", clone_url, workdir], check=True)

        # Build Docker image
        subprocess.run(["docker", "build", "-t", data.repo_name, workdir], check=True)

        # Assign random port
        port = random.randint(9000, 9999)
        container_name = f"{data.repo_name.replace('/', '_')}-{port}"

        container_id = deploy_container(
            image_name=data.repo_name,
            container_name=container_name,
            port=port
        )

        # Save to database
        app = App(
            name=data.repo_name,
            container_id=container_id,
            port=port
        )
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