<div align="center">

# 🛡️ mcp-chronoshell

The safety net for autonomous AI agents.

[![PyPI version](https://img.shields.io/pypi/v/mcp-chronoshell.svg)](https://pypi.org/project/mcp-chronoshell/)
[![Python versions](https://img.shields.io/pypi/pyversions/mcp-chronoshell.svg)](https://pypi.org/project/mcp-chronoshell/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**The safety net for autonomous AI agents.**

</div>

`mcp-chronoshell` is a Model Context Protocol (MCP) server that grants AI agents the ability to execute terminal commands with a built-in "Undo Button." By utilizing hyper-fast, state-reverting snapshots, agents can safely write code, manipulate files, and run scripts without the risk of permanently breaking your local workspace.

<video src="assets/recording.mp4" autoplay loop muted playsinline width="100%"></video>

## 🧠 How It Works: The Snapshot Architecture

When an agent is connected to Chronoshell, it gains access to a safe execution loop. The server exposes three primary tools to the LLM:

1. 📸 **`run_safe_command` (The Executor):** Before executing a shell command, the server takes a millisecond-fast snapshot of the current working directory, ignoring heavy directories (e.g., `node_modules`, `.venv`, `.git`).
2. ⏪ **`revert_workspace` (The Undo Button):** If the command exits with an error or causes unintended side effects, the agent can call this tool to instantly roll the directory back to its exact previous state.
3. 🗑️ **`commit_workspace` (The Garbage Collector):** If the command succeeds and the agent validates the output, it calls this tool to clear the snapshot cache and save disk space.

## ✨ Core Optimizations & Safety

* **Zero-Latency Backups:** Uses hardcoded blocklists and OS-level I/O optimizations to take snapshots in milliseconds, preventing the LLM from timing out.
* **Concurrent Multi-Agent Safety:** Injects cryptographic UUIDs into snapshot IDs, guaranteeing race-condition safety when multiple agents invoke commands simultaneously.
* **Smart Symlink Evasion:** Dynamically sniffs out and bypasses Windows Junctions and Reparse points to prevent infinite-loop crashes.
* **Actionable Error Routing:** Captures OS-level permission denials and `STDERR` outputs, routing them directly back into the LLM's context window so it can learn and adapt.

## 🚀 Installation

You can run `mcp-chronoshell` instantly via `uv` (recommended) or install it globally using `pip`:

```bash
# Using uv (Recommended)
uvx mcp-chronoshell

# Using pip
pip install mcp-chronoshell
```

## 🔌 Connecting to AI Clients

### 1. Google Antigravity (Workspace Local)

To give a specific Antigravity project access to the safety net, create a `.agents/mcp_config.json` file in the root of your project:

```json
{
  "mcpServers": {
    "chronoshell": {
      "command": "uvx",
      "args": ["mcp-chronoshell"]
    }
  }
}
```

### 2. Claude Desktop (Global)

Add the server to your Claude Desktop configuration file:

- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "chronoshell": {
      "command": "uvx",
      "args": ["mcp-chronoshell"]
    }
  }
}
```

### 3. Custom LangChain / Python Agents

Chronoshell is fully compatible with `langchain-mcp-adapters`. Simply initialize the `StdioServerParameters` pointing to the `uvx` command to bind the tools to your custom ReAct or LangGraph agents.

## 🤝 Contributing

Contributions are welcome! If you have ideas for new features, performance optimizations, or find a bug, please open an issue or submit a pull request.

## 📄 License

This project is licensed under the MIT License.
