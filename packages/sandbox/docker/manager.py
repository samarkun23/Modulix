import docker 
from docker.errors import (
    DockerException,
    APIError,
    ImageNotFound,
    NotFound
)

class DockerManager:
    
    MANAGED_BY = "autonomous-engineer"
    WORKSPACE_MOUNT = "/workspace"

    def __init__(self):
        self.client = docker.from_env()

    # 1. Check docker daemon
    def health_check(self):
        try:
            self.client.ping()
            return True
        except DockerException:
            return False
    
    # Ensuring image exist
    def ensure_image(self,image:str):
        try:
            return self.client.images.get(image)
        except ImageNotFound:
            return self.client.images.pull(image)
    
    def create_container(
        self,
        task_id: str,
        workspace_id: str,
        project_id: str,
        workspace_path: str,
        image: str = "python:3.12-slim"
    ):
        self.ensure_image(image)

        labels = {
            "managed-by": self.MANAGED_BY,
            "ae.task_id": task_id,
            "ae.workspace_id": workspace_id,
            "ae.project_id": project_id,
            "ae.version": "1",
        }

        container = self.client.containers.create(
            image = image,
            name = f"ae-task-{task_id}",
            command = [
                "sh",
                "-c",
                "while true; do sleep 3600; done"
            ],
            detach=True,
            working_dir = self.WORKSPACE_MOUNT,
            volumes = {
                workspace_path:{
                    "bind": self.WORKSPACE_MOUNT,
                    "mode": 'rw',
                }
            },

            labels=labels,

            # Resource limits
            mem_limit='1g',
            nano_cpus = 1_000_000_000,
            pids_limit=128,

            # Basic security
            cap_drop=["ALL"],
            security_opt=["no-new-privileges:true"],
        )
        return container
    
    # Start container
    def start_container(self,container_id:str):
        try:
            container = self.client.containers.get(container_id)
            container.start()
            return container
        except NotFound:
            raise ValueError( "container does not exist")
        except DockerException as e:
            raise RuntimeError(f"Failed to start container: {e}") from e

    def get_container(self,container_id:str):
        try:
            container = self.client.containers.get(container_id)
            container.reload()
            return{
                "id": container.id,
                "status": container.status,
                "labels": container.labels
            }
            
        except NotFound:
            return None
    
    def stop_container(self,container_id:str):
        try:
            container = self.client.containers.get(container_id)

            #Refresh container information from docker engine
            container.reload()

            if container.status == "running":
                container.stop(timeout=10)

            return True
        except NotFound:
            return False
    
    def remove_container(self,container_id):
        try:
            container = self.client.containers.get(container_id)
            container.remove(force=True)
            return True
        except NotFound:
            return False
    
    def list_managed_containers(self):
        containers = self.client.containers.list(
            all=True,
            filters={
                "label": f"managed-by={self.MANAGED_BY}"
            },
        )

        return[
            {
                "id": container.id,
                "status": container.status,
                "labels": container.labels,
            }
            for container in containers
        ]

    def close(self):
        self.client.close()





