# Project Brief: Standalone Python Cline Agent

## 1. Project Goal

The primary goal of this project is to create a standalone Python library that encapsulates the core functionality of the Cline agent. This library will provide a main `Agent` class with a `step` function, allowing developers to easily integrate Cline's agentic capabilities into their own Python applications.

## 2. Core Requirements

The Python library must replicate the following core functionalities from the existing TypeScript implementation:

*   **Agentic Loop:** The library must implement the core agentic loop, where the agent can make API requests, process responses, and execute tools in a cyclical manner.
*   **Tool Execution:** The library must support the execution of a core set of tools, including `execute_command`, `read_file`, `write_to_file`, and others as needed.
*   **API Provider Support:** The library should be designed to support multiple AI providers (e.g., Anthropic, OpenAI) through a modular `ApiHandler` system.
*   **State Management:** The library must manage the conversation state, including the user-facing messages and the API-level conversation history.
*   **Context Management:** The library must implement context management to handle conversation truncation and ensure that the context window of the language model is not exceeded.

## 3. High-Level Architecture

The Python library will follow a modular architecture, similar to the TypeScript implementation. The key components will be:

*   **`Agent` Class:** The main entry point for the library.
*   **`ToolExecutor` Class:** Responsible for executing tools.
*   **`ApiHandler` Class:** Responsible for communicating with AI providers.
*   **`MessageStateHandler` Class:** Responsible for managing the conversation state.
*   **`ContextManager` Class:** Responsible for managing the context window.
*   **`prompts` Module:** Responsible for generating the system prompt.
*   **`parsers` Module:** Responsible for parsing the assistant's response.

## 4. Key Deliverables

*   A standalone Python library, installable via `pip`.
*   A main `Agent` class with a `step` function.
*   A set of core tools for file system operations and command execution.
*   Support for at least one AI provider (e.g., Anthropic).
*   A comprehensive set of documentation in the memory bank.
