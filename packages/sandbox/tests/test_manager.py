

import pytest
from unittest.mock import MagicMock, patch

from docker.errors import DockerException, ImageNotFound, NotFound

from packages.sandbox.docker.manager import DockerManager


# --------------------------------------------------
# FIXTURE
# --------------------------------------------------

@pytest.fixture
def manager():
    with patch("packages.sandbox.docker.manager.docker.from_env") as mock_from_env:

        mock_client = MagicMock()
        mock_from_env.return_value = mock_client

        docker_manager = DockerManager()

        yield docker_manager



# --------------------------------------------------
# 1. INITIALIZATION TEST
# --------------------------------------------------

def test_manager_initialization(manager):
    assert manager.client is not None


# --------------------------------------------------
# 2. HEALTH CHECK TESTS
# --------------------------------------------------

def test_health_check_success(manager):
    manager.client.ping.return_value = True

    result = manager.health_check()

    assert result is True
    manager.client.ping.assert_called_once()


def test_health_check_failure(manager):
    manager.client.ping.side_effect = DockerException(
        "Docker daemon unavailable"
    )

    result = manager.health_check()

    assert result is False


# --------------------------------------------------
# 3. ENSURE IMAGE TESTS
# --------------------------------------------------

def test_ensure_image_exists(manager):
    mock_image = MagicMock()

    manager.client.images.get.return_value = mock_image

    result = manager.ensure_image("python:3.12-slim")

    assert result == mock_image

    manager.client.images.get.assert_called_once_with(
        "python:3.12-slim"
    )

    manager.client.images.pull.assert_not_called()


def test_ensure_image_pull_if_missing(manager):
    mock_image = MagicMock()

    manager.client.images.get.side_effect = ImageNotFound(
        "Image not found"
    )

    manager.client.images.pull.return_value = mock_image

    result = manager.ensure_image("python:3.12-slim")

    assert result == mock_image

    manager.client.images.pull.assert_called_once_with(
        "python:3.12-slim"
    )


# --------------------------------------------------
# 4. CREATE CONTAINER TESTS
# --------------------------------------------------

def test_create_container_success(manager, tmp_path):
    mock_container = MagicMock()

    manager.client.images.get.return_value = MagicMock()

    manager.client.containers.create.return_value = mock_container

    result = manager.create_container(
        task_id="task-123",
        workspace_id="workspace-123",
        project_id="project-123",
        workspace_path=str(tmp_path),
    )

    assert result == mock_container

    manager.client.containers.create.assert_called_once()

    kwargs = manager.client.containers.create.call_args.kwargs

    assert kwargs["image"] == "python:3.12-slim"

    assert kwargs["name"] == "ae-task-task-123"

    assert kwargs["working_dir"] == "/workspace"

    assert kwargs["mem_limit"] == "1g"

    assert kwargs["nano_cpus"] == 1_000_000_000

    assert kwargs["pids_limit"] == 128

    assert kwargs["cap_drop"] == ["ALL"]

    assert kwargs["security_opt"] == [
        "no-new-privileges:true"
    ]

    assert kwargs["labels"]["managed-by"] == (
        DockerManager.MANAGED_BY
    )

    assert kwargs["labels"]["ae.task_id"] == "task-123"

    assert kwargs["labels"]["ae.workspace_id"] == "workspace-123"

    assert kwargs["labels"]["ae.project_id"] == "project-123"

    assert kwargs["volumes"]["%s" % tmp_path] == {
        "bind": "/workspace",
        "mode": "rw"
    }


def test_create_container_pulls_missing_image(manager, tmp_path):
    manager.client.images.get.side_effect = ImageNotFound(
        "Image not found"
    )

    manager.client.images.pull.return_value = MagicMock()

    manager.client.containers.create.return_value = MagicMock()

    manager.create_container(
        task_id="task-1",
        workspace_id="workspace-1",
        project_id="project-1",
        workspace_path=str(tmp_path),
        image="python:3.12-slim"
    )

    manager.client.images.pull.assert_called_once_with(
        "python:3.12-slim"
    )


# --------------------------------------------------
# 5. START CONTAINER TESTS
# --------------------------------------------------

def test_start_container_success(manager):
    mock_container = MagicMock()

    manager.client.containers.get.return_value = mock_container

    result = manager.start_container("container-123")

    assert result == mock_container

    manager.client.containers.get.assert_called_once_with(
        "container-123"
    )

    mock_container.start.assert_called_once()


def test_start_container_not_found(manager):
    manager.client.containers.get.side_effect = NotFound(
        "Container not found"
    )

    with pytest.raises(ValueError, match="container does not exist"):
        manager.start_container("invalid-container")


def test_start_container_docker_error(manager):
    manager.client.containers.get.side_effect = DockerException(
        "Docker API error"
    )

    with pytest.raises(RuntimeError, match="Failed to start container"):
        manager.start_container("container-123")


# --------------------------------------------------
# 6. GET CONTAINER TESTS
# --------------------------------------------------

def test_get_container_success(manager):
    mock_container = MagicMock()

    mock_container.id = "container-123"
    mock_container.status = "running"

    mock_container.labels = {
        "managed-by": DockerManager.MANAGED_BY,
        "ae.workspace_id": "workspace-123"
    }

    manager.client.containers.get.return_value = mock_container

    result = manager.get_container("container-123")

    assert result["id"] == "container-123"

    assert result["status"] == "running"

    assert result["labels"] == mock_container.labels

    mock_container.reload.assert_called_once()


def test_get_container_not_found(manager):
    manager.client.containers.get.side_effect = NotFound(
        "Container not found"
    )

    result = manager.get_container("invalid-container")

    assert result is None


# --------------------------------------------------
# 7. STOP CONTAINER TESTS
# --------------------------------------------------

def test_stop_running_container(manager):
    mock_container = MagicMock()

    mock_container.status = "running"

    manager.client.containers.get.return_value = mock_container

    result = manager.stop_container("container-123")

    assert result is True

    mock_container.reload.assert_called_once()

    mock_container.stop.assert_called_once_with(timeout=10)


def test_stop_already_stopped_container(manager):
    mock_container = MagicMock()

    mock_container.status = "exited"

    manager.client.containers.get.return_value = mock_container

    result = manager.stop_container("container-123")

    assert result is True

    mock_container.stop.assert_not_called()


def test_stop_container_not_found(manager):
    manager.client.containers.get.side_effect = NotFound(
        "Container not found"
    )

    result = manager.stop_container("invalid-container")

    assert result is False


# --------------------------------------------------
# 8. REMOVE CONTAINER TESTS
# --------------------------------------------------

def test_remove_container_success(manager):
    mock_container = MagicMock()

    manager.client.containers.get.return_value = mock_container

    result = manager.remove_container("container-123")

    assert result is True

    mock_container.remove.assert_called_once_with(
        force=True
    )


def test_remove_container_not_found(manager):
    manager.client.containers.get.side_effect = NotFound(
        "Container not found"
    )

    result = manager.remove_container("invalid-container")

    assert result is False


# --------------------------------------------------
# 9. LIST MANAGED CONTAINERS TESTS
# --------------------------------------------------

def test_list_managed_containers(manager):
    container1 = MagicMock()

    container1.id = "container-1"
    container1.status = "running"
    container1.labels = {
        "managed-by": DockerManager.MANAGED_BY
    }

    container2 = MagicMock()

    container2.id = "container-2"
    container2.status = "exited"
    container2.labels = {
        "managed-by": DockerManager.MANAGED_BY
    }

    manager.client.containers.list.return_value = [
        container1,
        container2
    ]

    result = manager.list_managed_containers()

    assert len(result) == 2

    assert result[0]["id"] == "container-1"
    assert result[0]["status"] == "running"

    assert result[1]["id"] == "container-2"
    assert result[1]["status"] == "exited"

    manager.client.containers.list.assert_called_once_with(
        all=True,
        filters={
            "label": f"managed-by={DockerManager.MANAGED_BY}"
        }
    )


def test_list_managed_containers_empty(manager):
    manager.client.containers.list.return_value = []

    result = manager.list_managed_containers()

    assert result == []


# --------------------------------------------------
# 10. CLOSE DOCKER CLIENT TEST
# --------------------------------------------------

def test_close(manager):
    manager.close()

    manager.client.close.assert_called_once()
