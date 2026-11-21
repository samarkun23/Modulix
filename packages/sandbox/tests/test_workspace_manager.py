
import pytest

from workspace.manager import (
    WorkspaceManager,
    WorkspaceError,
    WorkspaceNotFoundError,
    WorkspaceSecurityError,
)


@pytest.fixture
def manager(tmp_path):
    return WorkspaceManager(str(tmp_path / "workspaces"))


def test_create_workspace(manager):
    result = manager.create_workspace("task_001")

    assert result["created"] is True
    assert manager.get_workspace("task_001")["exists"] is True


def test_duplicate_workspace(manager):
    manager.create_workspace("task_001")

    with pytest.raises(WorkspaceError):
        manager.create_workspace("task_001")


def test_write_and_read_file(manager):
    manager.create_workspace("task_001")

    manager.write_file(
        "task_001",
        "main.py",
        "print('Hello World')"
    )

    content = manager.read_file("task_001", "main.py")

    assert content == "print('Hello World')"


def test_nested_file_creation(manager):
    manager.create_workspace("task_001")

    manager.write_file(
        "task_001",
        "src/app/main.py",
        "print('Nested file')"
    )

    assert manager.read_file(
        "task_001",
        "src/app/main.py"
    ) == "print('Nested file')"


def test_path_traversal_blocked(manager):
    manager.create_workspace("task_001")

    with pytest.raises(WorkspaceSecurityError):
        manager.write_file(
            "task_001",
            "../../outside.txt",
            "malicious"
        )


def test_absolute_path_blocked(manager):
    manager.create_workspace("task_001")

    with pytest.raises(WorkspaceSecurityError):
        manager.write_file(
            "task_001",
            "/tmp/outside.txt",
            "malicious"
        )


def test_invalid_workspace_id(manager):
    with pytest.raises(WorkspaceSecurityError):
        manager.create_workspace("../outside")


def test_missing_workspace(manager):
    with pytest.raises(WorkspaceNotFoundError):
        manager.get_workspace("missing")


def test_file_size_limit(manager):
    manager.create_workspace("task_001")

    content = "a" * (manager.MAX_FILE_SIZE + 1)

    with pytest.raises(WorkspaceError):
        manager.write_file(
            "task_001",
            "large.txt",
            content
        )


def test_list_files(manager):
    manager.create_workspace("task_001")

    manager.write_file("task_001", "main.py", "print(1)")
    manager.write_file("task_001", "src/app.py", "print(2)")

    files = manager.list_files("task_001")

    assert "main.py" in files
    assert "src/app.py" in files


def test_delete_workspace(manager):
    manager.create_workspace("task_001")

    result = manager.delete_workspace("task_001")

    assert result["deleted"] is True

    with pytest.raises(WorkspaceNotFoundError):
        manager.get_workspace("task_001")


def test_symlink_blocked(manager, tmp_path):
    manager.create_workspace("task_001")

    outside = tmp_path / "outside.txt"
    outside.write_text("safe")

    workspace = tmp_path / "workspaces" / "task_001"

    (workspace / "link.txt").symlink_to(outside)

    with pytest.raises(WorkspaceSecurityError):
        manager.read_file("task_001", "link.txt")


def test_list_files_skips_symlinks(manager, tmp_path):
    manager.create_workspace("task_001")

    workspace = tmp_path / "workspaces" / "task_001"
    outside = tmp_path / "outside.txt"
    outside.write_text("secret")

    (workspace / "link.txt").symlink_to(outside)

    assert "link.txt" not in manager.list_files("task_001")
