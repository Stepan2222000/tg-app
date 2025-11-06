"""Filesystem helpers for screenshot storage."""

from pathlib import Path


def ensure_subdirectory(base_dir: Path, *parts: str) -> Path:
    """
    Ensure that a subdirectory exists under the given base directory.

    Args:
        base_dir: Root uploads directory (resolved path).
        *parts: Subsequent path components (e.g., user ID, assignment ID).

    Returns:
        Resolved Path of the created directory.
    """
    directory = base_dir.joinpath(*(str(part) for part in parts)).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def cleanup_empty_dirs(path: Path, stop_at: Path) -> None:
    """
    Remove empty directories up to (but not including) the stop_at directory.

    Args:
        path: Directory to start cleanup from (typically the assignment folder).
        stop_at: Root uploads directory to preserve.
    """
    current = path.resolve()
    stop = stop_at.resolve()

    # Only clean paths that are inside the uploads directory
    if stop not in current.parents and current != stop:
        return

    while current != stop:
        try:
            current.rmdir()
        except FileNotFoundError:
            # Directory already gone – continue to parent
            pass
        except OSError:
            # Directory not empty – stop cleanup
            break

        current = current.parent
        if stop not in current.parents and current != stop:
            break


def build_static_url(file_path: Path, base_dir: Path, mount: str = "/static/screenshots") -> str:
    """
    Build a static URL for a stored screenshot.

    Falls back to returning just the filename if the file is outside the uploads dir
    (for backward compatibility with legacy data).
    """
    resolved_base = base_dir.resolve()
    resolved_file = file_path.resolve()

    try:
        relative_path = resolved_file.relative_to(resolved_base)
        return f"{mount}/{relative_path.as_posix()}"
    except ValueError:
        return f"{mount}/{resolved_file.name}"
