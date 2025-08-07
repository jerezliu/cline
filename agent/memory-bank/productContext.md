# Product Context

## 1. Why This Project Exists

This project exists to provide a **lightweight, standalone Python library** that demonstrates the core agentic capabilities of the Cline ecosystem. It serves two main purposes:

1.  **Accessibility:** To make Cline's core agentic loop accessible to Python developers in a simple, easy-to-integrate library format, independent of the VS Code extension.
2.  **Foundation:** To serve as a clear, minimal implementation of an agent, which can be used as a foundation for more complex applications or as an educational tool.

## 2. Problems It Solves

*   **Complexity:** It offers a simplified, synchronous alternative to the fully-featured, asynchronous Cline extension, making it easier to understand the basic agentic flow.
*   **Integration:** Provides a simple Python-native way to embed Cline's core logic into other Python-based tools, scripts, and services.
*   **Portability:** It is not tied to any specific IDE or platform, running wherever Python is installed.

## 3. How It Should Work

The library provides a simple and intuitive API centered around the `Agent` class. A developer can instantiate the `Agent`, set its mode to either "plan" or "act", and then call its `step` method with user input.

*   In **"plan" mode**, the agent will engage in a dialogue to understand the problem and formulate a plan, returning its analysis as a text response.
*   In **"act" mode**, the agent will execute the plan, using its tools to perform actions and returning a final, consolidated response upon completion.

This dual-mode system provides a more structured and predictable interaction model, allowing developers to separate the planning and execution phases of a task.

## 4. User Experience Goals

*   **Ease of Use:** The library should be easy to install (`pip install cline-agent`) and use, with a minimal and clear API surface.
*   **Clarity:** The code should be easy to read and understand, serving as a reference implementation.
*   **Reliability:** The library should be reliable and robust within its defined scope, with comprehensive unit tests ensuring its core components function correctly.
