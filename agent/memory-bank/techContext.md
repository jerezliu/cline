# Tech Context

## 1. Core Technologies

*   **Python 3.8+:** The core programming language for the library.
*   **Pip:** The package installer for Python.
*   **Anthropic SDK:** The library uses the official `anthropic` Python client for API communication.

## 2. Development Environment

*   **Virtual Environment:** A virtual environment (e.g., `venv`) should be used to manage project dependencies.
*   **Code Formatter:** A code formatter such as `black` should be used to maintain a consistent code style.
*   **Linter:** A linter such as `flake8` or `pylint` should be used to identify potential errors and code quality issues.
*   **Testing:** The project uses the built-in `unittest` framework and `unittest.mock` for testing.

## 3. Docstring Format

*   **Google-style:** All docstrings should follow the Google-style format.

## 4. System Prompt Comparison

The system prompts of the Python agent and the production Cline extension differ significantly in their generation, content, and contextual awareness.

### Key Differences

| Feature | Python Agent | Production Cline (TypeScript) |
| :--- | :--- | :--- |
| **Generation** | **Static:** Prompts are hardcoded strings in `agent/prompts.py`. | **Dynamic:** Prompts are assembled at runtime from multiple sources. |
| **Tool Definitions** | **Basic:** Hardcoded with a name, description, and simple usage example. | **Rich & Extensible:** Detailed descriptions, structured parameter schemas, and dynamic injection of tools from MCP servers. |
| **Context** | **CLI-Focused:** Includes CWD, OS, shell, file listing, and git remotes. | **IDE-Focused & Comprehensive:** Includes CWD, OS, shell, `.clinerules`, open files, and terminal state. |
| **Architecture** | **Simple:** Reflects a basic agentic loop with Plan/Act modes. | **Complex:** Supports a sophisticated architecture with Plan/Act, MCP, and model-specific prompt variations. |

### Detailed Breakdown

#### Python Agent Prompt

*   **Nature:** **Unified and Dynamic.**
*   **Content:** The agent now uses a single, unified system prompt for both "plan" and "act" modes, mirroring the structure of the production Cline extension. Environment details are no longer part of the system prompt but are instead passed in the user message.
*   **Generation:** The `get_system_prompt()` function in `agent/prompts.py` constructs the system prompt, while the `EnvironmentManager` in `agent/environment.py` is responsible for gathering and formatting the environment details, which are then appended to the user's input in `agent/agent.py`.

#### Production Cline (TypeScript) Prompt

*   **Nature:** **Dynamic, Context-Aware, and Modular.**
*   **Content:** The prompt is constructed at runtime and is significantly more detailed. It includes:
    *   **Mode-Specific Instructions:** Different base prompts for **Plan Mode** vs. **Act Mode**.
    *   **Model-Specific Variations:** The core prompt can be specialized for different models (e.g., `claude4.ts`) to optimize performance.
    *   **Dynamic Tool Definitions:** A list of all available tools, including those from connected **MCP servers**, with detailed parameter schemas.
    *   **Custom Instructions:** Injects user-provided rules from `.clinerules/` files.
    *   **Comprehensive Environment Details:** Information about the user's OS, current working directory, shell, open files, and the state of active terminals.
*   **Generation:** The `SYSTEM_PROMPT` function in `src/core/prompts/system.ts` dynamically assembles these components, creating a highly contextual and powerful set of instructions for the agent.
