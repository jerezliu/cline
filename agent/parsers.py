import re
from typing import List, Dict, Union

# Type definitions to mirror the TypeScript types
class TextContent:
    def __init__(self, content: str, partial: bool):
        self.type = "text"
        self.content = content
        self.partial = partial

class ToolUse:
    def __init__(self, name: str, params: Dict[str, str], partial: bool):
        self.type = "tool_use"
        self.name = name
        self.params = params
        self.partial = partial

AssistantMessageContent = Union[TextContent, ToolUse]

def parse_assistant_message(assistant_message: str) -> List[AssistantMessageContent]:
    """
    Parses an assistant message string that may contain XML-based tool calls.
    """
    content_blocks: List[AssistantMessageContent] = []
    
    # Regex to find tool use blocks and surrounding text
    pattern = re.compile(r"(.*?)(<(\w+)>(.*?)</\3>)(.*)", re.DOTALL)
    
    match = pattern.search(assistant_message)
    
    if not match:
        # No tool use found, the whole message is text
        if assistant_message.strip():
            content_blocks.append(TextContent(content=assistant_message.strip(), partial=False))
        return content_blocks

    # Extract parts
    pre_text = match.group(1).strip()
    tool_block = match.group(2)
    tool_name = match.group(3)
    tool_content = match.group(4).strip()
    post_text = match.group(5).strip()

    if pre_text:
        content_blocks.append(TextContent(content=pre_text, partial=False))

    # Parse parameters from tool_content
    params = {}
    param_pattern = re.compile(r"<(\w+)>(.*?)</\1>", re.DOTALL)
    for param_match in param_pattern.finditer(tool_content):
        param_name = param_match.group(1)
        param_value = param_match.group(2).strip()
        params[param_name] = param_value
    
    content_blocks.append(ToolUse(name=tool_name, params=params, partial=False))

    if post_text:
        # Recursively parse the rest of the message
        content_blocks.extend(parse_assistant_message(post_text))

    return content_blocks
