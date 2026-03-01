import docker

client = docker.from_env()

def deploy_container(image_name: str, container_name: str, port: int):
    """
    Deploy container and expose port dynamically.
    Supports nginx-based images (static sites) and backend containers.
    """

    try:
        container = client.containers.run(
            image=image_name,
            name=container_name,
            detach=True,

            # Map container port 80 (nginx) to random host port
            ports={"80/tcp": port},

            mem_limit="512m",
            nano_cpus=500000000,  # 0.5 CPU
            restart_policy={"Name": "always"}
        )
        return container.id

    except docker.errors.APIError as e:
        raise Exception(f"Docker deploy failed: {str(e)}")


def stop_container(container_name: str):
    """
    Stop and remove container safely.
    """
    try:
        container = client.containers.get(container_name)
        container.stop()
        container.remove()
        return True
    except docker.errors.NotFound:
        return False