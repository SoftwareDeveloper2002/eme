import docker

client = docker.from_env()

def deploy_container(image_name: str, container_name: str, port: int):
    container = client.containers.run(
        image=image_name,
        name=container_name,
        detach=True,
        ports={'8000/tcp': port},
        mem_limit="512m",
        nano_cpus=500000000,  # 0.5 CPU
        restart_policy={"Name": "always"}
    )
    return container.id


def stop_container(container_name: str):
    container = client.containers.get(container_name)
    container.stop()
    container.remove()