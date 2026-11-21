import os
import re
import shutil
import tempfile

from pathlib import Path

class WorkspaceError(Exception):
    """Base execption for workspace operations"""

class WorkspaceNotFoundError(WorkspaceError):
    pass

class WorkspaceSecurityError(WorkspaceError):
    pass

class WorkspaceManager:

    MAX_FILE_SIZE = 10 * 1024 * 1024 # 10 mb

    def __init__(self,base_dir: str = "./workspaces"):
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _validate_workspace_id(self,workspace_id:str):
        
        if not isinstance(workspace_id,str):
            raise WorkspaceSecurityError("Invalide workspace Id")

        if not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", workspace_id):
            raise WorkspaceSecurityError("Invalide workspace Id")

    def _get_workspace_path(self,workspace_id: str) -> Path:
        
        self._validate_workspace_id(workspace_id)

        workspace_path = self.base_dir / workspace_id

        if workspace_path.is_symlink(): # If workspace is a shortcut then just throw error bec someone cannot access to sensitive folder instead of workspace
            raise WorkspaceSecurityError(
                "Workspace cannot be symlink"
            )

        if workspace_path.parent != self.base_dir: # if workspace path parent is not equal to base-dir then throw error
            raise WorkspaceSecurityError(
                "Workspace is outside base directory"
            )

        return workspace_path

    def _get_safe_file_path(
        self,
        workspace_id: str,
        file_path:str
    ) -> Path:
        workspace = self._get_workspace_path(workspace_id)

        if not workspace.is_dir():
            raise WorkspaceNotFoundError(
                f"Workspace not found: {workspace_id}"
            )

        if not isinstance(file_path, str) or not file_path:
            raise WorkspaceSecurityError("Ivalid file path")

        relative_path = Path(file_path)

        if relative_path.is_absolute():
            raise WorkspaceSecurityError(
                "Absolute paths are not allowed"
            )

        if ".." in relative_path.parts:
            raise WorkspaceSecurityError(
                "Path traversal detected" 
            )

        if not relative_path.parts :
            raise WorkspaceSecurityError("Invalid file path")

        current = workspace
        # Reject symlink component
        for part in relative_path.parts:

            if part in ("","."):
                continue
            
            current = current / part

            if current.is_symlink():
                raise WorkspaceSecurityError(
                    "Symlink are not allowed"
                )

        resolve = current.resolve(strict=False)

        if not resolve.is_relative_to(workspace):
            raise WorkspaceSecurityError(
                "Path escape workspace"
            )

        return current

    def create_workspace(self,workspace_id: str):
        workspace = self._get_workspace_path(workspace_id)

        if workspace.exists():
            raise WorkspaceError(f"Workspace already exists: {workspace_id}")

        workspace.mkdir(parents=False, exist_ok=False)

        return{
            "workspace_id": workspace_id,
            "path": str(workspace),
            "created": True
        }
    
    # get workspace
    def get_workspace(self,workspace_id:str):
        workspace = self._get_workspace_path(workspace_id)

        if not workspace.is_dir():
            raise WorkspaceNotFoundError(
                f"Workspace not found : {workspace_id}"
            )


        return {
            "workspace_id": workspace_id,
            "path": str(workspace),
            "exists": True
        }

    def write_file(
        self,
        workspace_id: str,
        file_path: str,
        content: str
    ):
        if not isinstance(content, str):
            raise WorkspaceError(
                "Content must be a string"
            )

        content_bytes = content.encode("utf-8")

        if len(content_bytes) > self.MAX_FILE_SIZE:
            raise WorkspaceError(
                "File exceeds maximum size limit"
            )

        target = self._get_safe_file_path(
            workspace_id,
            file_path
        )

        target.parent.mkdir(parents=True, exist_ok=True)

        # revalidate after dir created
        target = self._get_safe_file_path(
            workspace_id,
            file_path
        )

        # Atomic file replacement
        temp_path = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=target.parent,
                delete=False
            ) as temp_file:
                temp_file.write(content_bytes)
                temp_path = Path(temp_file.name)
            
            os.replace(temp_path,target)
        
        finally:
            if temp_path and temp_path.exists():
                temp_path.unlink()

        return {
            "path": file_path,
            "written": True,
            "size": len(content_bytes),
        }
    
    def read_file(
        self,
        workspace_id: str,
        file_path: str
    ):
        target = self._get_safe_file_path(
            workspace_id,
            file_path
        )

        if not target.is_file():
            raise WorkspaceNotFoundError(f"File not found: {file_path}")

        if target.stat().st_size > self.MAX_FILE_SIZE:
            raise WorkspaceError(
                "File exceeds maximum size limit"
            )

        return target.read_text(encoding="utf-8")
    
    def list_files(self,workspace_id: str):
        workspace = self._get_workspace_path(workspace_id)

        if not workspace.is_dir():
            raise WorkspaceNotFoundError(f"Workspace not found: {workspace_id}")

        files = []

        for root,dirs,filenames in os.walk(
            workspace,
            followlinks=False
        ):
            root_path = Path(root)

            # do not traverse symlink directories 
            dirs[:] = [
                directory
                for directory in dirs
                if not (root_path/directory).is_symlink()
            ]
            
            for filename in filenames:
                file = root_path / filename

                if file.is_symlink():
                    continue

                if file.is_file():
                    files.append(
                        str(file.relative_to(workspace))
                    )

        return sorted(files)

    def delete_workspace(self,workspace_id: str):
        workspace = self._get_workspace_path(workspace_id)

        if not workspace.is_dir():
            raise WorkspaceNotFoundError(
                f"Workspace not found: {workspace_id}"
            )

        shutil.rmtree(workspace) # removing directory and it's content

        return {
            "workspace_id": workspace_id,
            "deleted": True
        }





