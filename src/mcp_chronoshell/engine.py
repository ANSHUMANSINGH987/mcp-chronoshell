import shutil
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

SNAPSHOT_BASE_DIR = Path(".chronoshell_snapshots")
STATE_FILE = SNAPSHOT_BASE_DIR / "latest.txt"

IGNORE_DIRS = {
    '.git', '.venv', 'venv', 'env', 'node_modules', 
    '__pycache__', '.pytest_cache', '.tox', 
    'dist', 'build', '.chronoshell_snapshots'
}

def _ignore_heavy_dirs(dir_path: str, contents: list[str]) -> list[str]:
    """
    Callback for shutil.copytree. 
    Filters out heavy or temporary directories to ensure snapshots take milliseconds.
    """
    return [item for item in contents if item in IGNORE_DIRS]

def take_snapshot() -> str:
    """
    Creates a backup of the current workspace state.
    
    Returns:
        str: The unique timestamp ID of the snapshot.
    """
    SNAPSHOT_BASE_DIR.mkdir(exist_ok=True)
    
    snapshot_id = str(int(time.time() * 1000))
    target_dir = SNAPSHOT_BASE_DIR / snapshot_id
    
    logger.info(f"Taking workspace snapshot: {snapshot_id}")
    
    try:
        shutil.copytree(".", target_dir, ignore=_ignore_heavy_dirs)
        STATE_FILE.write_text(snapshot_id)
        return snapshot_id
    except Exception as e:
        logger.error(f"Failed to take snapshot: {e}")
        raise RuntimeError(f"Snapshot failed: {e}")

def restore_latest_snapshot() -> tuple[bool, str]:
    """
    Overwrites the current workspace with the most recent snapshot.
    
    Returns:
        tuple[bool, str]: Success status and an accompanying message.
    """
    if not STATE_FILE.exists():
        return False, "No recent snapshot state file found."
        
    snapshot_id = STATE_FILE.read_text().strip()
    snapshot_path = SNAPSHOT_BASE_DIR / snapshot_id
    
    if not snapshot_path.exists():
        return False, f"Snapshot data directory '{snapshot_id}' is missing."
        
    logger.warning(f"Reverting workspace to snapshot: {snapshot_id}")
    
    try:
        shutil.copytree(snapshot_path, ".", ignore=_ignore_heavy_dirs, dirs_exist_ok=True)
        return True, snapshot_id
    except Exception as e:
        logger.error(f"Failed to restore snapshot: {e}")
        return False, str(e)

def commit_workspace() -> None:
    """
    Wipes the snapshot cache. Called when the agent is confident the command worked.
    """
    if SNAPSHOT_BASE_DIR.exists():
        logger.info("Committing workspace and clearing snapshot cache.")
        shutil.rmtree(SNAPSHOT_BASE_DIR)
