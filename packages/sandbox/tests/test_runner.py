import pytest
from unittest.mock import Mock

from docker.errors import DockerException, NotFound

from executor.runner import (
    Runner,
    RunnerError,
    ContainerNotRunningError,
    CommandValidationError,
)


@pytest.fixture
def docker_manager():
    manager = Mock()
    return manager


@pytest.fixture
def runner(docker_manager):
    return Runner(docker_manager)


@pytest.fixture
def mock_container(docker_manager):
    container = Mock()
    container.status = "running"

    docker_manager.client.containers.get.return_value = container

    return container


def make_exec_result(
    exit_code=0,
    stdout=b"Hello",
    stderr=b"",
):
    result = Mock()
    result.exit_code = exit_code
    result.output = (stdout, stderr)
    return result


# -----------------------------------------
# 1. Successful command execution
# -----------------------------------------

@pytest.mark.asyncio
async def test_execute_success(runner, mock_container):
    mock_container.exec_run.return_value = make_exec_result(
        exit_code=0,
        stdout=b"Hello World",
        stderr=b"",
    )

    result = await runner.execute(
        container_id="container-123",
        command=["echo", "Hello World"],
    )

    assert result.exit_code == 0
    assert result.stdout == "Hello World"
    assert result.stderr == ""
    assert result.timed_out is False
    assert result.duration >= 0

    mock_container.exec_run.assert_called_once()


# -----------------------------------------
# 2. Command returns non-zero exit code
# -----------------------------------------

@pytest.mark.asyncio
async def test_execute_non_zero_exit(runner, mock_container):
    mock_container.exec_run.return_value = make_exec_result(
        exit_code=1,
        stdout=b"",
        stderr=b"Something went wrong",
    )

    result = await runner.execute(
        container_id="container-123",
        command=["python", "main.py"],
    )

    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr == "Something went wrong"
    assert result.timed_out is False


# -----------------------------------------
# 3. Command timeout
# -----------------------------------------

@pytest.mark.asyncio
async def test_execute_timeout(runner, mock_container):
    mock_container.exec_run.return_value = make_exec_result(
        exit_code=124,
        stdout=b"",
        stderr=b"Command timed out",
    )

    result = await runner.execute(
        container_id="container-123",
        command=["python", "infinite_loop.py"],
        timeout=5,
    )

    assert result.exit_code == 124
    assert result.timed_out is True

    args = mock_container.exec_run.call_args
    wrapped_command = args.kwargs["cmd"]

    assert "5s" in wrapped_command


# -----------------------------------------
# 4. Container does not exist
# -----------------------------------------

@pytest.mark.asyncio
async def test_execute_container_not_found(runner, docker_manager):
    docker_manager.client.containers.get.side_effect = NotFound(
        "Container not found"
    )

    with pytest.raises(RunnerError):
        await runner.execute(
            container_id="invalid-container",
            command=["echo", "hello"],
        )


# -----------------------------------------
# 5. Container is not running
# -----------------------------------------

@pytest.mark.asyncio
async def test_execute_container_not_running(
    runner,
    docker_manager,
):
    container = Mock()
    container.status = "exited"

    docker_manager.client.containers.get.return_value = container

    with pytest.raises(ContainerNotRunningError):
        await runner.execute(
            container_id="container-123",
            command=["echo", "hello"],
        )

    container.exec_run.assert_not_called()


# -----------------------------------------
# 6. Docker API error
# -----------------------------------------

@pytest.mark.asyncio
async def test_execute_docker_error(runner, docker_manager):
    docker_manager.client.containers.get.side_effect = DockerException(
        "Docker daemon unavailable"
    )

    with pytest.raises(RunnerError):
        await runner.execute(
            container_id="container-123",
            command=["echo", "hello"],
        )


# -----------------------------------------
# 7. Invalid empty command
# -----------------------------------------

@pytest.mark.asyncio
async def test_execute_empty_command(runner):
    with pytest.raises(CommandValidationError):
        await runner.execute(
            container_id="container-123",
            command=[],
        )


# -----------------------------------------
# 8. Invalid command argument type
# -----------------------------------------

@pytest.mark.asyncio
async def test_execute_invalid_command_type(runner):
    with pytest.raises(CommandValidationError):
        await runner.execute(
            container_id="container-123",
            command="echo hello",
        )


# -----------------------------------------
# 9. Command contains non-string argument
# -----------------------------------------

@pytest.mark.asyncio
async def test_execute_non_string_argument(runner):
    with pytest.raises(CommandValidationError):
        await runner.execute(
            container_id="container-123",
            command=["echo", 123],
        )


# -----------------------------------------
# 10. Invalid timeout values
# -----------------------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "timeout",
    [
        0,
        -1,
        999999,
        float("inf"),
        float("nan"),
        True,
        "10",
    ],
)
async def test_execute_invalid_timeout(runner, timeout):
    with pytest.raises(CommandValidationError):
        await runner.execute(
            container_id="container-123",
            command=["echo", "hello"],
            timeout=timeout,
        )


# -----------------------------------------
# 11. None output handling
# -----------------------------------------

@pytest.mark.asyncio
async def test_execute_none_output(runner, mock_container):
    mock_container.exec_run.return_value = make_exec_result(
        exit_code=0,
        stdout=None,
        stderr=None,
    )

    result = await runner.execute(
        container_id="container-123",
        command=["echo", "hello"],
    )

    assert result.stdout == ""
    assert result.stderr == ""


# -----------------------------------------
# 12. Verify working directory
# -----------------------------------------

@pytest.mark.asyncio
async def test_execute_uses_workspace_directory(
    runner,
    mock_container,
):
    mock_container.exec_run.return_value = make_exec_result()

    await runner.execute(
        container_id="container-123",
        command=["pwd"],
    )

    kwargs = mock_container.exec_run.call_args.kwargs

    assert kwargs["workdir"] == "/workspace"
    assert kwargs["demux"] is True
    assert kwargs["tty"] is False