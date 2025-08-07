# Active Context

## 1. Current Work Focus

The current focus is on understanding and documenting the significant architectural differences between the Python agent and the original TypeScript Cline agent. A detailed analysis of these differences has been completed and stored in `agent/memory-bank/deviations.md`.

## 2. Recent Changes

*   **API Request Parity:** The agent has been refactored to achieve API request parity with the TypeScript agent. This involved several key changes:
    *   **In-Prompt Tool Emulation:** The `ApiHandler` was modified to remove the native `tools` parameter, and a new XML parser was implemented in `parsers.py` to handle tool responses from the model's text output.
    *   **System Prompt Replication:** The system prompt from the TypeScript agent was ported to `claude4_prompt_template.py` and integrated into the `prompts.py` module.
    *   **Environment Context Replication:** The `environment.py` module was enhanced to gather and format environment context in the same way as the TypeScript agent.
*   **Agent Divergence Analysis:** A comprehensive deep-dive was performed to compare the Python and TypeScript agents. This analysis identified fundamental differences in system prompt construction, tool handling, context management, and API request logic. The findings are documented in `agent/memory-bank/deviations.md`.
*   **CLI-Native Plan/Act Mode:** The Plan/Act feature was refactored to be controlled by explicit user commands (`/plan`, `/act`), making it suitable for a command-line environment.
*   **Prompt Generation Alignment:** The Python agent's prompt generation has been refactored to align with the TypeScript agent. This includes unifying the system prompt, standardizing tool formatting, and relocating environment details to the user message.
*   **Test Suite Refinements:** The test suite has been updated to reflect the prompt generation changes and to fix import errors that were causing test failures.

## 3. Next Steps: Verification and Validation

The next step is to verify that the refactored agent is working as expected and to validate that it can successfully complete a simple task. This will involve:

*   **Running the test suite:** Ensure that all existing tests pass after the refactoring.
*   **Creating a new test case:** Write a new test case that specifically validates the new in-prompt tool emulation by running a simple "Hello, World!" task.
*   **Updating documentation:** Update the rest of the memory bank to reflect the new architecture.

## 4. Active Decisions and Considerations

*   **Fundamental API Request Divergence:** The Python and TypeScript agents send fundamentally different requests to the LLM. This is the most critical architectural divergence.
    *   **Python Agent:** Uses the LLM's **native tool-use** API. It sends a structured `tools` parameter containing a JSON schema for each tool. The system prompt is minimal.
    *   **TypeScript Agent:** **Emulates tool use via in-prompt instructions.** It injects detailed tool descriptions and XML usage examples directly into a large, context-rich system prompt.

*   **System Prompt and Context Injection:**
    *   **Python Agent:** Uses a static prompt template. Environment details are appended to the user's message. It does not support `.clinerules`.
    *   **TypeScript Agent:** Uses a highly dynamic prompt that embeds system information, environmental context, and custom instructions from `.clinerules` directly into the prompt.

*   **Feature and Tool Gaps:** The Python agent has a much smaller, hardcoded toolset and lacks many core features of the production agent, such as checkpoints, a user approval flow for tools, and robust error handling.

*   **Architectural Philosophy:** The recent refactoring has solidified a clear architectural philosophy for the Python agent: modular, single-responsibility components. This should guide future development, especially if the decision is made to upgrade the `ContextManager`.
