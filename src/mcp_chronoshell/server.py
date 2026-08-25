import os
import shutil
import subprocess
import time
import asyncio
import uuid
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

# Initialize the FastMCP server
mcp = FastMCP("Chronoshell")

# Hidden directory to store state snapshots
SNAPSHOT_DIR = ".chronoshell_snapshots"

# Optimized ignore list for hyper-fast O(1) snapshots
IGNORE_LIST = {".git", ".venv", "node_modules", "__pycache__", "dist", "build", ".chronoshell_snapshots"}

def ignore_heavy_dirs(dir_path, contents):
    """Callback for shutil.copytree to ignore heavy directories and infinite loop traps."""
    # 1. Start with our hardcoded blocklist
    ignored = [c for c in contents if c in IGNORE_LIST]
    
    # 2. Dynamically detect Windows Junctions and Symlinks
    for c in contents:
        full_path = os.path.join(dir_path, c)
        try:
            # lstat reads the item itself, without following where it points
            st = os.lstat(full_path)
            
            # Windows Reparse Points (Junctions) always have the 1024 attribute (0x400)
            is_reparse_point = hasattr(st, 'st_file_attributes') and (st.st_file_attributes & 1024)
            
            if is_reparse_point or os.path.islink(full_path):
                ignored.append(c)
        except Exception:
            pass # If we can't read it, it's safer to let the engine try to handle it
            
    return ignored

@mcp.tool()
async def run_safe_command(command: str) -> dict:
    """
    Executes a shell command safely. 
    Automatically creates a state-revert snapshot before execution.
    It enforces a 120-second timeout to prevent hangs.
    """
    # 1. Create the snapshot asynchronously with a timestamp + random 8-character UUID
    snapshot_id = f"{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
    current_snapshot_path = os.path.join(SNAPSHOT_DIR, snapshot_id)
    
    try:
        # Run blocking I/O in a separate thread to keep the server responsive
        await asyncio.to_thread(
            shutil.copytree,
            ".", 
            current_snapshot_path, 
            ignore=ignore_heavy_dirs, 
            dirs_exist_ok=True,
            symlinks=True
        )
    except Exception as e:
        raise ToolError(f"Failed to create workspace snapshot: {str(e)}")

    # 2. Execute the shell command asynchronously
    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            # Enforce 120-second timeout
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120.0)
        except asyncio.TimeoutError:
            process.kill()
            raise ToolError(f"Command timed out after 120 seconds. If it caused partial damage, call revert_workspace().")

        output = stdout.decode('utf-8')
        error_output = stderr.decode('utf-8')
        exit_code = process.returncode

        # 3. Format context-aware LLM output
        result_text = f"Exit Code: {exit_code}\n"
        if output:
            result_text += f"\nSTDOUT:\n{output}"
        if error_output:
            result_text += f"\nSTDERR:\n{error_output}"
            
        result_text += f"\n\n[SYSTEM]: Snapshot '{snapshot_id}' created. If the command caused unintended side effects, call revert_workspace() immediately."
        
        return {"result": result_text}

    except Exception as e:
        raise ToolError(f"Command execution failed: {str(e)}")


@mcp.tool()
async def revert_workspace() -> dict:
    """
    Reverts the local directory to the exact state it was in before the last run_safe_command was executed.
    Call this IMMEDIATELY if the previous command failed, deleted files, or broke the code.
    Do NOT call this if the previous command succeeded.
    """
    if not os.path.exists(SNAPSHOT_DIR):
        raise ToolError("No snapshots found. Cannot revert.")
        
    snapshots = sorted(os.listdir(SNAPSHOT_DIR))
    if not snapshots:
        raise ToolError("Snapshot directory is empty. Cannot revert.")
        
    latest_snapshot = snapshots[-1]
    snapshot_path = os.path.join(SNAPSHOT_DIR, latest_snapshot)
    
    try:
        await asyncio.to_thread(
            shutil.copytree,
            snapshot_path, 
            ".", 
            dirs_exist_ok=True,
            symlinks=True 
        )
        return {"result": f"Workspace successfully reverted to state prior to snapshot {latest_snapshot}."}
    except Exception as e:
        raise ToolError(f"Rollback failed during file copy: {str(e)}")


@mcp.tool()
async def commit_workspace() -> dict:
    """
    Clears the snapshot cache to save disk space. 
    Call this ONLY when you have verified that the previous commands succeeded and did exactly what was intended.
    """
    if os.path.exists(SNAPSHOT_DIR):
        try:
            await asyncio.to_thread(shutil.rmtree, SNAPSHOT_DIR)
            return {"result": "Workspace committed. Snapshot cache cleared."}
        except Exception as e:
            raise ToolError(f"Failed to clear cache: {str(e)}")
    return {"result": "No snapshot cache found to commit."}