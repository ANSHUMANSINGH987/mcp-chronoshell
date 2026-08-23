<h1 align="center">⏳ MCP Chronoshell</h1>

<p align="center">
  <strong>A state-reverting terminal MCP that gives AI agents an "undo button" for local file operations.</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/mcp-chronoshell/"><img src="https://img.shields.io/pypi/v/mcp-chronoshell.svg" alt="PyPI version"></a>
  <a href="https://pypi.org/project/mcp-chronoshell/"><img src="https://img.shields.io/pypi/pyversions/mcp-chronoshell.svg" alt="Python Versions"></a>
  <a href="https://github.com/"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
  <a href="https://pypi.org/project/fastmcp/"><img src="https://img.shields.io/badge/Powered%20by-FastMCP-ff69b4.svg" alt="Powered by FastMCP"></a>
</p>

---

## 🚀 The Problem

Giving an autonomous agent access to your local terminal is risky. One hallucinated `rm -rf`, a malformed `sed` command, or a botched configuration change can break your workspace. While Docker-based sandboxes provide security isolation, they prevent the agent from actually helping you build software on your local host (like running `uv add`, modifying `settings.py`, or refactoring your repository).

## 💡 The Solution

**MCP Chronoshell** acts as a wrapper around standard terminal execution. Before executing any command, it takes a hyper-fast snapshot of your current working directory (intelligently ignoring heavy folders like `node_modules`, `.venv`, and `.git`). 

If the agent makes a mistake, it can invoke a `revert_workspace` tool to instantly time-travel back to the pre-execution state. 

It provides **productivity with a safety net**.

---

## ⚡ Features

- **Safe Execution (`run_safe_command`)**: Wraps every command in a pre-execution snapshot.
- **Instant Rollbacks (`revert_workspace`)**: Undoes accidental deletions, broken code edits, or bad package installs.
- **Context-Aware Outputs**: Structures `stdout` and `stderr` specifically for LLM consumption.
- **Hyper-Fast I/O Engine**: Utilizes $O(1)$ set lookups to ignore heavy, reproducible directories so snapshots take milliseconds.
- **Cross-Platform**: Works flawlessly on Windows, macOS, Linux, and WSL environments.

---

## 📦 Installation

Since MCP Chronoshell is published on PyPI, installation is trivial. It is highly recommended to use `uv` for lightning-fast installation, but standard `pip` works perfectly as well.

```bash
# Using uv (Recommended)
uv tool install mcp-chronoshell

# Using pip
pip install mcp-chronoshell
```

---

## 🛠️ Configuration (Claude Desktop)

To use Chronoshell with Claude Desktop, you need to add it to your MCP client configuration. 

Open your Claude Desktop configuration file:
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

Add the following JSON block. Make sure to update the `command` path to point to where Python or `uv` is installed on your machine.

```json
{
  "mcpServers": {
    "chronoshell": {
      "command": "mcp-chronoshell",
      "args": []
    }
  }
}
```
*Note: If `mcp-chronoshell` is not in your global system PATH, provide the absolute path to your python executable or uv binary, and pass `["-m", "mcp_chronoshell.server"]` as the arguments.*

---

## 🧰 Available Agent Tools

Once connected, your AI agent will have access to the following native tools:

1. `run_safe_command(command: str)`
   Executes a shell command safely. Automatically creates a state-revert snapshot before execution. It prevents hanging by enforcing a 120-second timeout.
   
2. `revert_workspace()`
   Reverts the local directory to the exact state it was in before the last `run_safe_command` was executed. The agent is instructed to call this immediately if a command caused unintended side effects.
   
3. `commit_workspace()`
   Clears the snapshot cache (`.chronoshell_snapshots/`) to save disk space. Called when the agent verifies the previous commands succeeded.

---

## 🏗️ Architecture Under the Hood

Chronoshell is built entirely in Python using **FastMCP**, meaning it requires zero external dependencies like Docker or Redis. 
- It uses Python's `shutil.copytree` with `dirs_exist_ok=True` (introduced in Python 3.8) to act as a highly efficient overwrite/merge mechanism.
- Snapshots are stored locally in a hidden `.chronoshell_snapshots` directory.
- A hardcoded blocklist ensures that $I/O$ bottlenecks (like `__pycache__` or `node_modules`) are strictly ignored during the snapshot phase, preserving terminal speed.

---

## 🤝 Contributing

Contributions are welcome! If you want to optimize the snapshot engine (e.g., implementing an optional Git-based snapshot mode) or add new terminal capabilities:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License & Author

**Author:** Anshuman Singh  
**License:** Distributed under the MIT License. See `LICENSE` for more information.