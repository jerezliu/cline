from typing import List, Dict, Any

class ToolParameter:
    """A parameter for a tool."""
    def __init__(self, name: str, param_type: str, description: str, required: bool):
        self.name = name
        self.param_type = param_type
        self.description = description
        self.required = required

    def to_dict(self) -> Dict[str, Any]:
        """Converts the parameter to a dictionary."""
        return {
            "name": self.name,
            "type": self.param_type,
            "description": self.description,
            "required": self.required,
        }

class Tool:
    """A tool that the agent can use."""
    def __init__(self, name: str, description: str, parameters: List[ToolParameter]):
        self.name = name
        self.description = description
        self.parameters = parameters

    def to_dict(self) -> Dict[str, Any]:
        """Converts the tool to a dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": [p.to_dict() for p in self.parameters],
        }

    def to_json_schema(self) -> Dict[str, Any]:
        """Converts the tool to a JSON schema dictionary for native tool use."""
        properties = {
            param.name: {"type": param.param_type, "description": param.description}
            for param in self.parameters
        }
        required = [param.name for param in self.parameters if param.required]

        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }

def get_tools() -> List[Tool]:
    """Returns a list of all available tools."""
    return [
        Tool(
            name="read_file",
            description="Reads the content of a file at the specified path. Use this when you need to examine the contents of an existing file.",
            parameters=[
                ToolParameter(name="path", param_type="string", description="The path of the file to read.", required=True),
            ],
        ),
        Tool(
            name="write_to_file",
            description="Writes content to a file at the specified path. If the file exists, it will be overwritten. If it does not exist, it will be created.",
            parameters=[
                ToolParameter(name="path", param_type="string", description="The path of the file to write to.", required=True),
                ToolParameter(name="content", param_type="string", description="The content to write to the file.", required=True),
            ],
        ),
        Tool(
            name="replace_in_file",
            description="Request to replace sections of content in an existing file using SEARCH/REPLACE blocks that define exact changes to specific parts of the file.",
            parameters=[
                ToolParameter(name="path", param_type="string", description="The path of the file to modify.", required=True),
                ToolParameter(name="diff", param_type="string", description="One or more SEARCH/REPLACE blocks.", required=True),
            ],
        ),
        Tool(
            name="search_files",
            description="Request to perform a regex search across files in a specified directory, providing context-rich results.",
            parameters=[
                ToolParameter(name="path", param_type="string", description="The path of the directory to search in.", required=True),
                ToolParameter(name="regex", param_type="string", description="The regular expression pattern to search for.", required=True),
                ToolParameter(name="file_pattern", param_type="string", description="Glob pattern to filter files (e.g., '*.ts' for TypeScript files).", required=False),
            ],
        ),
        Tool(
            name="web_fetch",
            description="Fetches content from a specified URL and processes into markdown.",
            parameters=[
                ToolParameter(name="url", param_type="string", description="The URL to fetch content from.", required=True),
            ],
        ),
        Tool(
            name="list_code_definition_names",
            description="Request to list definition names (classes, functions, methods, etc.) used in source code files at the top level of the specified directory.",
            parameters=[
                ToolParameter(name="path", param_type="string", description="The path of the directory to list top level source code definitions for.", required=True),
            ],
        ),
        Tool(
            name="browser_action",
            description="Request to interact with a Puppeteer-controlled browser.",
            parameters=[
                ToolParameter(name="action", param_type="string", description="The action to perform.", required=True),
                ToolParameter(name="url", param_type="string", description="URL to launch the browser at.", required=False),
                ToolParameter(name="coordinate", param_type="string", description="x,y coordinates.", required=False),
                ToolParameter(name="text", param_type="string", description="Text to type.", required=False),
            ],
        ),
        Tool(
            name="use_mcp_tool",
            description="Request to use a tool provided by a connected MCP server.",
            parameters=[
                ToolParameter(name="server_name", param_type="string", description="The name of the MCP server providing the tool.", required=True),
                ToolParameter(name="tool_name", param_type="string", description="The name of the tool to execute.", required=True),
                ToolParameter(name="arguments", param_type="string", description="A JSON object containing the tool's input parameters.", required=True),
            ],
        ),
        Tool(
            name="access_mcp_resource",
            description="Request to access a resource provided by a connected MCP server.",
            parameters=[
                ToolParameter(name="server_name", param_type="string", description="The name of the MCP server providing the resource.", required=True),
                ToolParameter(name="uri", param_type="string", description="The URI identifying the specific resource to access.", required=True),
            ],
        ),
        Tool(
            name="load_mcp_documentation",
            description="Load documentation about creating MCP servers.",
            parameters=[],
        ),
        Tool(
            name="new_task",
            description="Request to create a new task with preloaded context.",
            parameters=[
                ToolParameter(name="Context", param_type="string", description="The context to preload the new task with.", required=True),
            ],
        ),
        Tool(
            name="attempt_completion",
            description="Present the result of your work to the user.",
            parameters=[
                ToolParameter(name="result", param_type="string", description="The result of the task.", required=True),
                ToolParameter(name="command", param_type="string", description="A CLI command to execute to show a live demo of the result.", required=False),
            ],
        ),
        Tool(
            name="list_files",
            description="Lists files and directories within a specified directory.",
            parameters=[
                ToolParameter(name="path", param_type="string", description="The path of the directory to list.", required=True),
                ToolParameter(name="recursive", param_type="boolean", description="Whether to list files recursively. Defaults to False.", required=False),
            ],
        ),
        Tool(
            name="execute_command",
            description="Executes a shell command on the system. Use this to perform system operations, run scripts, or interact with the command line.",
            parameters=[
                ToolParameter(name="command", param_type="string", description="The shell command to execute.", required=True),
            ],
        ),
        Tool(
            name="plan_mode_respond",
            description="Respond to the user with your thoughts, analysis, questions, or a proposed plan. This is your only way to communicate in plan mode.",
            parameters=[
                ToolParameter(name="response", param_type="string", description="The content of your response to the user.", required=True),
            ],
        ),
    ]
