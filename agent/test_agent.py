import unittest
from unittest.mock import patch, MagicMock
from cline.agent.agent import Agent
from cline.agent.message_state_handler import MessageStateHandler
from cline.agent.tools import get_tools

@patch('cline.agent.agent.get_system_prompt')
@patch('cline.agent.agent.ApiHandler')
@patch('cline.agent.agent.ToolExecutor')
@patch('cline.agent.agent.ContextManager')
@patch('cline.agent.agent.MessageStateHandler')
class TestAgent(unittest.TestCase):
    """Tests for the Agent class."""

    def test_initialization(self, MockMessageStateHandler, MockContextManager, MockToolExecutor, MockApiHandler, mock_get_system_prompt):
        """Test that the Agent initializes correctly."""
        agent = Agent(api_configuration={})
        self.assertIsInstance(agent, Agent)
        self.assertEqual(agent.mode, "act")
        MockApiHandler.assert_called_once_with({})
        MockToolExecutor.assert_called_once_with(agent.tools)
        MockContextManager.assert_called_once()
        MockMessageStateHandler.assert_called_once()

    def test_set_mode(self, MockMessageStateHandler, MockContextManager, MockToolExecutor, MockApiHandler, mock_get_system_prompt):
        """Test the set_mode method."""
        agent = Agent(api_configuration={})
        agent.set_mode("plan")
        self.assertEqual(agent.mode, "plan")
        agent.set_mode("act")
        self.assertEqual(agent.mode, "act")
        with self.assertRaises(ValueError):
            agent.set_mode("invalid_mode")

    def test_step_with_text_response(self, MockMessageStateHandler, MockContextManager, MockToolExecutor, MockApiHandler, mock_get_system_prompt):
        """Test the step method with a simple text response."""
        mock_api_handler = MockApiHandler.return_value
        mock_message_state_handler = MockMessageStateHandler.return_value
        mock_context_manager = MockContextManager.return_value

        # The API handler returns the raw text from the model
        mock_response = MagicMock()
        mock_response.content = [MagicMock(type='text', text='Hello, world!')]
        mock_api_handler.create_message.return_value = mock_response
        mock_context_manager.get_truncated_conversation_history.return_value = []
        mock_message_state_handler.api_conversation_history = []

        agent = Agent(api_configuration={})
        response = agent.step("Hello")

        # The step method should return the parsed text
        self.assertEqual(response, "Hello, world!")
        
        mock_message_state_handler.add_cline_message.assert_called()
        mock_api_handler.create_message.assert_called_once()
        mock_get_system_prompt.assert_called_with(agent.tools)

    def test_step_in_plan_mode(self, MockMessageStateHandler, MockContextManager, MockToolExecutor, MockApiHandler, mock_get_system_prompt):
        """Test that the correct system prompt is used in plan mode."""
        mock_api_handler = MockApiHandler.return_value
        mock_context_manager = MockContextManager.return_value
        mock_message_state_handler = MockMessageStateHandler.return_value

        mock_response = MagicMock()
        mock_response.content = [MagicMock(type='text', text='I have a plan.')]
        mock_api_handler.create_message.return_value = mock_response
        mock_context_manager.get_truncated_conversation_history.return_value = []
        mock_message_state_handler.api_conversation_history = []

        agent = Agent(api_configuration={})
        agent.set_mode("plan")
        agent.step("Let's make a plan.")

        mock_get_system_prompt.assert_called_with(agent.tools)

    def test_step_with_tool_use(self, MockMessageStateHandler, MockContextManager, MockToolExecutor, MockApiHandler, mock_get_system_prompt):
        """Test the step method with a tool use response."""
        mock_api_handler = MockApiHandler.return_value
        mock_tool_executor = MockToolExecutor.return_value
        mock_message_state_handler = MockMessageStateHandler.return_value
        mock_context_manager = MockContextManager.return_value

        # Mock the API response to include a tool use block on the first call,
        # and a text response on the second call.
        mock_tool_response = MagicMock()
        mock_tool_response.content = [MagicMock(type='text', text='<write_to_file><path>hello.txt</path><content>Hello, World!</content></write_to_file>')]
        
        mock_text_response = MagicMock()
        mock_text_response.content = [MagicMock(type='text', text='File written.')]

        mock_api_handler.create_message.side_effect = [mock_tool_response, mock_text_response]
        
        # Mock the tool executor to return a specific result
        mock_tool_executor.execute_tool.return_value = "File written successfully."

        mock_context_manager.get_truncated_conversation_history.return_value = []
        mock_message_state_handler.api_conversation_history = []

        agent = Agent(api_configuration={})
        agent.step("Write Hello, World! to hello.txt")

        # Verify that the tool executor was called with the correct parameters
        mock_tool_executor.execute_tool.assert_called_once_with(
            "write_to_file",
            {"path": "hello.txt", "content": "Hello, World!"}
        )

if __name__ == '__main__':
    unittest.main()
