import asyncio
import math
import time


from dataclasses import dataclass
from typing import Optional

from docker.errors import DockerException, NotFound

class RunnerError(Exception):
    """Base exception for execution errors."""

class ContainerNotRunningError(RunnerError):
    pass

class CommandValidationError(RunnerError):
    pass

@dataclass
class ExecutionResult:
    exit_code: int
    stdout: str
    stderr: str
    duration: float
    timed_out: bool

    def to_dict(self):
        return {
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration": self.duration,
            "timed_out": self.timed_out
        }
    
class Runner:
    WORKING_DIRECTORY = "./workspace"
    MAX_TIMEOUT = 600
    KILL_AFTER = 5

    def __init__(self, docker_manager):
        self.docker_manager = docker_manager
    
    def _validate_command(self, command, timeout):
        if(
            not isinstance(command, (list,tuple))
            or not command
            or not all (
                isinstance(arg,str) and arg
                for arg in command
            )
        ):
            raise CommandValidationError(
                "Command must be a non-empty list of strings"
            )
        
        if (
            isinstance(timeout, bool)
            or not isinstance(timeout, (int,float))
            or not math.isfinite(timeout)
            or timeout <= 0
            or timeout > self.MAX_TIMEOUT
        ):
            raise CommandValidationError(
                f"Timeout must be between 0 and {self.MAX_TIMEOUT} seconds"
            )
        
    # Decode docker output
    @staticmethod
    def _decode_output(output):
        if output is None:
            return ""
        
        if isinstance(output,bytes):
            return output.decode(
                "utf-8",
                errors="replace"
            )
        
        return str(output)
    
    # Execute command synchronously
    def _execute_sync(
        self,
        container_id: str,
        command: list,
        timeout: float
    ):
        start_time = time.monotonic()
        
        try:
            container = (
                self.docker_manager.client.containers.get(container_id)
            )

            container.reload()
            
            if container.status != "running":
                raise ContainerNotRunningError(
                    f"Container is not running: {container_id}"
                )
            
            # GNU coreutils timeout protects execution
            # from running indefinitely.
            wrapped_command = [
                "timeout",
                "--signal=TERM",
                f"--kill-after={self.KILL_AFTER}s",
                f"{timeout:g}s",
                *command
            ]

            result = container.exec_run(
                cmd=wrapped_command,
                workdir=self.WORKING_DIRECTORY,
                stdout=True,
                stderr=True,
                demux=True,
                tty=False
            )
            
            stdout, stderr = result.output

            duration = time.monotonic() - start_time

            exit_code = result.exit_code

            # GNU timeout returns 124 when the
            # timeout limit is reached
            timed_out = exit_code == 124

            return ExecutionResult(
                exit_code = exit_code,
                stdout=self._decode_output(stdout),
                stderr=self._decode_output(stderr),
                duration=round(duration,3),
                timed_out=timed_out
            )
        
        except NotFound as exc:
            raise RunnerError(
                f"Contianer not found: {container_id}"
            ) from exc
        
        except DockerException as exc:
            raise RunnerError(
                f"Docker execution failed: {str(exc)}"
            ) from exc
        
    # pubic async execution method 
    async def execute(
        self,
        container_id: str,
        command: list,
        timeout: float = 60
    ) -> ExecutionResult:
        self._validate_command(command, timeout)

        # TODO: Need to see this one more time 

        return await asyncio.to_thread(
            self._execute_sync,
            container_id,
            command,
            timeout 
        )        