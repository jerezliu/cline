import os
from typing import List
from .tools import Tool
from .claude4_prompt_template import SYSTEM_PROMPT_CLAUDE4, get_browser_action_prompt

def get_system_prompt(tools: List[Tool], supports_browser_use: bool = True) -> str:
    """
    Returns the appropriate system prompt based on the agent's mode.

    Args:
        tools (List[Tool]): The list of available tools.
        supports_browser_use (bool): Whether the agent supports browser use.

    Returns:
        str: The system prompt.
    """
    browser_settings = {"viewport": {"width": 1280, "height": 800}}
    
    # We will manually replace the placeholders to avoid format string errors.
    prompt = SYSTEM_PROMPT_CLAUDE4
    prompt = prompt.replace("{cwd}", os.getcwd())
    prompt = prompt.replace("{os_name}", os.name)
    prompt = prompt.replace("{shell}", os.environ.get("SHELL", "bash"))
    prompt = prompt.replace("{home_dir}", os.path.expanduser("~"))

    browser_action_prompt = get_browser_action_prompt(supports_browser_use, browser_settings)
    
    # Insert browser_action_prompt before the web_fetch tool
    # This is a bit of a hack, but it's the easiest way to do it for now.
    # A better solution would be to make the entire tool section dynamic.
    prompt_parts = prompt.split("## web_fetch")
    
    return prompt_parts[0] + browser_action_prompt + "## web_fetch" + prompt_parts[1]
