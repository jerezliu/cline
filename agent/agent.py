import json
from .api_handler import ApiHandler
from .context_manager import ContextManager
from .message_state_handler import MessageStateHandler
from .tool_executor import ToolExecutor
from .prompts import get_system_prompt
from .tools import get_tools
from .environment import EnvironmentManager
from .parsers import parse_assistant_message


class Agent:
    """The main Agent class for the Cline Python library."""

    def __init__(self, api_configuration):
        """Initializes the Agent.

        Args:
            api_configuration: The API configuration.
        """
        self.api_configuration = api_configuration
        self.api_handler = ApiHandler(api_configuration)
        self.message_state_handler = MessageStateHandler()
        self.tools = get_tools()
        self.tool_executor = ToolExecutor(self.tools)
        self.env_manager = EnvironmentManager()
        self.context_manager = ContextManager(
            client=self.api_handler.client,
            model=self.api_handler.api_configuration.get("model", "claude-3-haiku-20240307")
        )
        self.mode = "act"  # Default to "act" mode

    def set_mode(self, mode: str):
        """Sets the agent's mode.

        Args:
            mode: The mode to set ("plan" or "act").
        """
        if mode not in ["plan", "act"]:
            raise ValueError("Mode must be either 'plan' or 'act'")
        self.mode = mode

    def step(self, user_input: str):
        """Performs one step of the agentic loop.

        Args:
            user_input: The user's input.

        Returns:
            The agent's response.
        """
        # Handle mode-switching commands
        if user_input.strip() == "/plan":
            self.set_mode("plan")
            response = "Switched to PLAN MODE. How can I help you plan?"
            self.message_state_handler.add_cline_message({"role": "assistant", "content": response})
            return response
        elif user_input.strip() == "/act":
            self.set_mode("act")
            response = "Switched to ACT MODE. I will now execute the plan."
            self.message_state_handler.add_cline_message({"role": "assistant", "content": response})
            # In a real CLI, we might proceed directly into the loop here,
            # but for library usage, returning a confirmation is cleaner.
            return response

        environment_details = self.env_manager.get_environment_details(self.mode)
        full_user_input = f"{user_input}\n{environment_details}"
        self.message_state_handler.add_cline_message({"role": "user", "content": full_user_input})
        self.message_state_handler.add_api_conversation_history({"role": "user", "content": full_user_input})

        while True:
            truncated_history = self.context_manager.get_truncated_conversation_history(
                self.message_state_handler.api_conversation_history,
                max_tokens=128000  # Placeholder
            )
            system_prompt = get_system_prompt(self.tools)

            response = self.api_handler.create_message(system_prompt, truncated_history)

            assistant_response_text = ""
            if response.content and response.content[0].type == "text":
                assistant_response_text = response.content[0].text

            self.message_state_handler.add_api_conversation_history({
                "role": "assistant",
                "content": assistant_response_text
            })

            parsed_content = parse_assistant_message(assistant_response_text)
            
            tool_results = []
            text_response = ""
            has_tool_use = False

            for block in parsed_content:
                if block.type == "tool_use":
                    has_tool_use = True
                    result = self.tool_executor.execute_tool(block.name, block.params)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": "unknown", # This will need to be improved
                        "content": str(result),
                    })
                elif block.type == "text":
                    text_response += block.content

            if has_tool_use:
                self.message_state_handler.add_api_conversation_history({
                    "role": "user",
                    "content": tool_results
                })
            else:
                self.message_state_handler.add_cline_message({"role": "assistant", "content": text_response})
                return text_response
