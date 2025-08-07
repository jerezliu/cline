import unittest
from unittest.mock import MagicMock, patch

from .agent import Agent
from .prompts import get_system_prompt
from .tools import get_tools, Tool, ToolParameter

class TestReplication(unittest.TestCase):
    def test_system_prompt_replication(self):
        """Tests that the generated system prompt matches the golden fixture."""
        tools = get_tools()
        
        # Create the "golden" tool string part
        tool_strings = []
        for tool in tools:
            params_str = "\n".join(
                f"- {p.name}: ({'required' if p.required else 'optional'}) {p.description}"
                for p in tool.parameters
            )
            tool_strings.append(f"""## {tool.name}
Description: {tool.description}
Parameters:
{params_str}
Usage:
<{tool.name}>
...
</{tool.name}>""")
        golden_tool_str = "\n\n".join(tool_strings)

        # Create the full golden prompt
        from .prompt_template import SYSTEM_PROMPT_TEMPLATE
        golden_prompt = SYSTEM_PROMPT_TEMPLATE.format(tools_string=golden_tool_str)

        # Generate the prompt using the function
        generated_prompt = get_system_prompt(tools)

        # Assert they are identical
        self.assertEqual(generated_prompt, golden_prompt)

    def test_tool_to_json_schema(self):
        """Tests that the to_json_schema method produces the correct format."""
        tool = Tool(
            name="test_tool",
            description="A test tool.",
            parameters=[
                ToolParameter(name="param1", param_type="string", description="A required string parameter.", required=True),
                ToolParameter(name="param2", param_type="integer", description="An optional integer parameter.", required=False),
            ],
        )

        expected_schema = {
            "name": "test_tool",
            "description": "A test tool.",
            "parameters": {
                "type": "object",
                "properties": {
                    "param1": {"type": "string", "description": "A required string parameter."},
                    "param2": {"type": "integer", "description": "An optional integer parameter."},
                },
                "required": ["param1"],
            },
        }

        self.assertEqual(tool.to_json_schema(), expected_schema)

    @patch('agent.api_handler.anthropic')
    @patch('agent.agent.ContextManager')
    @patch('agent.agent.ToolExecutor')
    @patch('agent.agent.ApiHandler')
    def test_native_tool_use_loop(self, MockApiHandler, MockToolExecutor, MockContextManager, mock_anthropic):
        """Tests the full agent loop with native tool use."""
        # 1. Setup Mocks
        mock_api_handler = MockApiHandler.return_value
        mock_tool_executor = MockToolExecutor.return_value
        mock_context_manager = MockContextManager.return_value
        mock_context_manager.get_truncated_conversation_history.side_effect = lambda history, max_tokens: history

        # Mock API response for a tool call
        mock_tool_call = MagicMock()
        mock_tool_call.type = "tool_use"
        mock_tool_call.name = "read_file"
        mock_tool_call.input = {"path": "/test.txt"}
        mock_tool_call.id = "tool_call_123"

        # Mock API responses
        mock_tool_use_response = MagicMock()
        mock_tool_use_response.stop_reason = "tool_use"
        mock_tool_use_response.content = [mock_tool_call]

        mock_text_response = MagicMock()
        mock_text_response.stop_reason = "end_turn"
        text_block = MagicMock()
        text_block.type = "text"
        text_block.text = "Final response."
        mock_text_response.content = [text_block]

        mock_api_handler.create_message.side_effect = [
            mock_tool_use_response,
            mock_text_response,
        ]

        # Mock tool execution result
        mock_tool_executor.execute_tool.return_value = "file content"

        # 2. Initialize Agent
        agent = Agent(api_configuration={'api_key': 'test', 'model': 'test_model'})
        agent.api_handler = mock_api_handler
        agent.tool_executor = mock_tool_executor
        agent.context_manager = mock_context_manager

        # 3. Run one step
        agent.step("read the file /test.txt")

        # 4. Assertions
        # Assert API was called correctly
        self.assertEqual(mock_api_handler.create_message.call_count, 2)
        
        # Check the first call to the API
        first_call_args = mock_api_handler.create_message.call_args_list[0].args
        self.assertEqual(len(first_call_args), 3) # system_prompt, conversation_history, tools
        tools_arg = first_call_args[2]
        self.assertIsInstance(tools_arg, list)
        self.assertEqual(len(tools_arg), len(get_tools()))

        # Assert tool was executed correctly
        mock_tool_executor.execute_tool.assert_called_once_with("read_file", {"path": "/test.txt"})

        # Assert conversation history is structured correctly
        history = agent.message_state_handler.api_conversation_history
        self.assertEqual(len(history), 4)
        
        # Initial user message
        self.assertEqual(history[0]['role'], 'user')
        
        # Assistant's tool_use message
        self.assertEqual(history[1]['role'], 'assistant')
        self.assertEqual(history[1]['content'][0].type, 'tool_use')
        self.assertEqual(history[1]['content'][0].id, 'tool_call_123')

        # User's tool_result message
        self.assertEqual(history[2]['role'], 'user')
        self.assertEqual(history[2]['content'][0]['type'], 'tool_result')
        self.assertEqual(history[2]['content'][0]['tool_use_id'], 'tool_call_123')
        self.assertEqual(history[2]['content'][0]['content'], 'file content')

        # Final assistant text message
        self.assertEqual(history[3]['role'], 'assistant')
        self.assertEqual(history[3]['content'][0].type, 'text')
        self.assertEqual(history[3]['content'][0].text, 'Final response.')

if __name__ == '__main__':
    unittest.main()
