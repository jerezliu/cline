import os
import re
import subprocess
from typing import List, Dict, Any
from .tools import Tool


class ToolExecutor:
    """Executes tools for the Cline agent."""

    def __init__(self, tools: List[Tool]):
        """Initializes the ToolExecutor.

        Args:
            tools (List[Tool]): A list of Tool objects.
        """
        self._tools = {tool.name: getattr(self, f"_{tool.name}") for tool in tools}

    def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]):
        """Executes a tool.

        Args:
            tool_name: The name of the tool to execute.
            tool_input: The input for the tool.

        Returns:
            The result of the tool execution.
        """
        if tool_name in self._tools:
            return self._tools[tool_name](tool_input)
        else:
            return f"Tool '{tool_name}' not found."

    def _read_file(self, tool_input):
        """Reads the contents of a file.

        Args:
            tool_input: A dictionary containing the file path.

        Returns:
            The contents of the file.
        """
        try:
            with open(tool_input["path"], "r") as f:
                return f.read()
        except Exception as e:
            return str(e)

    def _write_to_file(self, tool_input):
        """Writes content to a file.

        Args:
            tool_input: A dictionary containing the file path and content.

        Returns:
            A message indicating the result of the operation.
        """
        try:
            with open(tool_input["path"], "w") as f:
                f.write(tool_input["content"])
            return f"Successfully wrote to {tool_input['path']}."
        except Exception as e:
            return str(e)

    def _web_fetch(self, tool_input):
        """Fetches and parses a URL."""
        try:
            import requests
            from bs4 import BeautifulSoup

            url = tool_input["url"]
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            return soup.get_text()
        except Exception as e:
            return str(e)

    def _search_files(self, tool_input):
        """Searches for a regex pattern in files."""
        try:
            path = tool_input.get("path", ".")
            regex = tool_input["regex"]
            file_pattern = tool_input.get("file_pattern")

            results = []
            for root, _, files in os.walk(path):
                for name in files:
                    if file_pattern:
                        import fnmatch
                        if not fnmatch.fnmatch(name, file_pattern):
                            continue
                    
                    file_path = os.path.join(root, name)
                    try:
                        with open(file_path, "r", errors='ignore') as f:
                            content = f.read()
                            if re.search(regex, content):
                                results.append(file_path)
                    except Exception:
                        # Ignore files that can't be opened
                        pass
            return results
        except Exception as e:
            return str(e)

    def _replace_in_file(self, tool_input):
        """Replaces content in a file based on SEARCH/REPLACE blocks."""
        try:
            path = tool_input["path"]
            diff = tool_input["diff"]

            with open(path, "r") as f:
                content = f.read()

            # Simple parser for SEARCH/REPLACE blocks
            parts = diff.split("=======")
            search_block = parts[0].replace("------- SEARCH", "").strip()
            replace_block = parts[1].replace("+++++++ REPLACE", "").strip()

            if search_block not in content:
                return f"Error: SEARCH block not found in {path}."

            content = content.replace(search_block, replace_block)

            with open(path, "w") as f:
                f.write(content)

            return f"Successfully applied changes to {path}."
        except Exception as e:
            return str(e)

    def _list_files(self, tool_input):
        """Lists files in a directory.

        Args:
            tool_input: A dictionary containing the path and a boolean for recursive.

        Returns:
            A list of files.
        """
        path = tool_input.get("path", ".")
        recursive = tool_input.get("recursive", False)
        try:
            if recursive:
                file_list = []
                for root, _, files in os.walk(path):
                    for name in files:
                        file_list.append(os.path.join(root, name))
                return file_list
            else:
                return os.listdir(path)
        except Exception as e:
            return str(e)

    def _list_code_definition_names(self, tool_input):
        """Returns a placeholder message indicating the tool is not implemented."""
        return "Tool 'list_code_definition_names' is not implemented yet."

    def _browser_action(self, tool_input):
        """Returns a placeholder message indicating the tool is not implemented."""
        return "Tool 'browser_action' is not implemented yet."

    def _use_mcp_tool(self, tool_input):
        """Returns a placeholder message indicating the tool is not implemented."""
        return "Tool 'use_mcp_tool' is not implemented yet."

    def _access_mcp_resource(self, tool_input):
        """Returns a placeholder message indicating the tool is not implemented."""
        return "Tool 'access_mcp_resource' is not implemented yet."

    def _load_mcp_documentation(self, tool_input):
        """Returns a placeholder message indicating the tool is not implemented."""
        return "Tool 'load_mcp_documentation' is not implemented yet."

    def _new_task(self, tool_input):
        """Returns a placeholder message indicating the tool is not implemented."""
        return "Tool 'new_task' is not implemented yet."

    def _attempt_completion(self, tool_input):
        """Returns a placeholder message indicating the tool is not implemented."""
        return "Tool 'attempt_completion' is not implemented yet."

    def _plan_mode_respond(self, tool_input):
        """Handles the response in plan mode.

        Args:
            tool_input: A dictionary containing the response.

        Returns:
            The response from the agent.
        """
        return tool_input.get("response", "")

    def _execute_command(self, tool_input):
        """Executes a shell command.

        Args:
            tool_input: A dictionary containing the command.

        Returns:
            The output of the command.
        """
        try:
            result = subprocess.run(
                tool_input["command"],
                shell=True,
                capture_output=True,
                text=True,
            )
            return result.stdout or result.stderr
        except Exception as e:
            return str(e)
