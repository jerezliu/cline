# System Patterns

## 1. Python Agent Architecture

The Python Cline agent follows a modular, backend-only architecture. It is designed as a self-contained library with clear separation of concerns.

*   **`Agent`:** The central orchestrator of the agentic loop. It now includes a **Plan/Act mode**, controlled by explicit user commands (`/plan`, `/act`), to separate the planning and execution phases of a task.
*   **`ToolExecutor`:** A dedicated component for executing a predefined set of tools. It is not mode-aware.
*   **`PromptBuilder`:** This component is no longer mode-aware. It constructs a single, unified system prompt, and the agent's mode is now communicated to the model via the `environment_details` block in the user message.
*   **`ApiHandler`:** A component for interacting with a single AI provider API (Anthropic).
*   **`MessageStateHandler`:** An in-memory component for managing the conversation state for the duration of the agent's lifecycle.
*   **`ContextManager`:** A component for truncating conversation history to prevent context window overflows.

The data flows in a unidirectional, synchronous manner. The `Agent.step()` method initiates a blocking loop that continues until a final text response is ready to be returned.

## 2. Comparison with Production Cline (TypeScript/VSCode)

While the Python agent implements the core conceptual loop, it deviates significantly from the production Cline extension. The production version is a full-featured, asynchronous, and stateful system.

### Key Architectural Deviations

The Python agent and the production TypeScript agent have significant architectural differences. A comprehensive breakdown of these differences is documented in `agent/memory-bank/deviations.md`. The most critical divergences are:

*   **API Request Formulation:** The two agents send fundamentally different requests to the LLM.
    *   **Python Agent:** Uses the LLM's **native tool-use** API, sending a structured `tools` parameter with a JSON schema. The system prompt is minimal.
    *   **TypeScript Agent:** **Emulates tool use via in-prompt instructions.** It injects detailed tool descriptions and XML usage examples directly into a large, context-rich system prompt and does not use the native `tools` parameter.

*   **System Prompt & Context:**
    *   **Python Agent:** Uses a static prompt template and appends environment details to the user's message.
    *   **TypeScript Agent:** Uses a highly dynamic prompt that embeds system information, environmental context (like open files and running terminals), and custom instructions from `.clinerules` directly into the system prompt.

*   **Context Management:**
    *   **Python Agent:** Performs simple linear truncation of the oldest messages.
    *   **TypeScript Agent:** Employs a sophisticated context optimization strategy that includes removing duplicate file reads and adaptively truncating history based on token savings.

## 3. Design Patterns

*   **Strategy Pattern:** The production `ApiHandler` uses the strategy pattern to support multiple AI providers. The Python agent has a single strategy.
*   **Singleton Pattern:** The production `McpHub` and `Controller` act as singletons to manage global state and connections.
*   **Observer Pattern:** The production system uses observers for real-time notifications from MCP servers and file system watchers.

## 4. Standalone Agent Limitations

As a standalone library, the Python agent cannot access VSCode-specific APIs. The following context information, available to the TypeScript agent, is considered out of scope for the current implementation and is deferred to a future project:

*   **VSCode Editor State:** Information about visible files and open tabs.
*   **Live Terminal State:** The ability to monitor actively running terminals and their real-time output.
*   **External File Modifications:** The ability to watch for file changes made outside of the agent's own tool executions.
