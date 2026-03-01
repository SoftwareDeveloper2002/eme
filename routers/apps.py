from fastapi import APIRouter
from docker_manager import deploy_container
import random

router = APIRouter()

@router.post("/deploy")
def deploy_app(app_name: str):
    port = random.randint(9000, 9999)
    container_name = f"{app_name}-{port}"

    container_id = deploy_container(
        image_name="nginx",
        container_name=container_name,
        port=port
    )

    return {
        "message": "App deployed",
        "container_id": container_id,
        "port": port
    }