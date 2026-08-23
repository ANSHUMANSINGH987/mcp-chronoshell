import subprocess
import logging
from pydantic import Field
from fastmcp import FastMCP

from mcp_chronoshell import engine

# Configure logging for the server operations
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Initialize the FastMCP server
mcp = FastMCP("Chronoshell")

@mcp.tool()
def run_safe_command(
    command: str = Field(description="The shell command to execute in the terminal (e.g., 'npm install', 'python script.py', 'sed -i ...').")
) -> str:
    """
    Executes a shell command safely. Automatically creates a state-revert snapshot before execution.
    Use this for any command that modifies files, installs packages, or could potentially break the workspace.
    """
    logger.info(f"Agent requested to run: {command}")
    
    try:
        # 1. Take the snapshot before anything runs
        snapshot_id = engine.take_snapshot()
    except Exception as e:
        return f"[SYSTEM ERROR] Failed to take snapshot. Command execution aborted to ensure safety: {e}"
    
    try:
        # 2. Execute the command
        # timeout=120 prevents the agent from hanging forever if a command prompts for input
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=120
        )
        
        # 3. Format output specifically for LLM consumption
        output_lines = [
            f"Exit Code: {result.returncode}",
        ]
        
        if result.stdout:
            output_lines.append("--- STDOUT ---")
            output_lines.append(result.stdout.strip())
            
        if result.stderr:
            output_lines.append("--- STDERR ---")
            output_lines.append(result.stderr.strip())
            
        # Append the critical safety reminder
        output_lines.append(f"\n[SYSTEM]: Snapshot '{snapshot_id}' created. If the output above looks wrong or caused side effects, call revert_workspace() immediately.")
        
        return "\n".join(output_lines)
        
    except subprocess.TimeoutExpired:
        return f"[SYSTEM WARNING] Command timed out after 120 seconds. State backed up in snapshot {snapshot_id}. You may want to revert."
    except Exception as e:
        return f"[SYSTEM ERROR] Execution failed: {str(e)}"


@mcp.tool()
def revert_workspace() -> str:
    """
    Reverts the local directory to the exact state it was in before the last run_safe_command was executed.
    Call this immediately if a command failed, deleted files, or caused unintended side effects.
    """
    logger.info("Agent requested workspace revert.")
    success, message = engine.restore_latest_snapshot()
    
    if success:
        return f"✅ CRITICAL RECOVERY SUCCESS: Workspace reverted to snapshot {message}. The bad changes have been undone."
    return f"❌ RECOVERY FAILED: {message}"


@mcp.tool()
def commit_workspace() -> str:
    """
    Clears the snapshot cache to save disk space. Call this ONLY when you have verified that the previous commands succeeded and did exactly what was intended.
    """
    logger.info("Agent requested snapshot commit.")
    engine.commit_workspace()
    return " Workspace changes committed. Snapshot cache cleared."


def main():
    """Entry point for the PyPI CLI script."""
    mcp.run()

if __name__ == "__main__":
    main()