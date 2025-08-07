import unittest
from unittest.mock import MagicMock, patch
from cline.agent import Agent

class TestPlanActMode(unittest.TestCase):

    def setUp(self):
        """Set up the test environment before each test."""
        # Provide a dummy api_key to prevent KeyError during initialization
        self.api_config = {"provider": "mock", "api_key": "dummy_key"}
        self.agent = Agent(self.api_config)
        # Mock the ApiHandler to avoid actual API calls
        self.agent.api_handler = MagicMock()

    def test_initial_mode(self):
        """Test that the agent initializes in 'act' mode by default."""
        self.assertEqual(self.agent.mode, "act")

    def test_set_mode_plan(self):
        """Test switching to 'plan' mode."""
        self.agent.set_mode("plan")
        self.assertEqual(self.agent.mode, "plan")

    def test_set_mode_act(self):
        """Test switching back to 'act' mode."""
        self.agent.set_mode("plan")
        self.agent.set_mode("act")
        self.assertEqual(self.agent.mode, "act")

    def test_set_invalid_mode(self):
        """Test that setting an invalid mode raises a ValueError."""
        with self.assertRaises(ValueError):
            self.agent.set_mode("invalid_mode")

    @patch('cline.agent.prompts.get_system_prompt')
    def test_step_plan_command(self, mock_get_prompt):
        """Test the '/plan' command changes mode and returns confirmation."""
        response = self.agent.step("/plan")
        self.assertEqual(self.agent.mode, "plan")
        self.assertEqual(response, "Switched to PLAN MODE. How can I help you plan?")
        # Ensure no API call is made when just switching modes
        self.agent.api_handler.create_message.assert_not_called()

    @patch('cline.agent.prompts.get_system_prompt')
    def test_step_act_command(self, mock_get_prompt):
        """Test the '/act' command changes mode and returns confirmation."""
        self.agent.set_mode('plan') # Start in plan mode
        response = self.agent.step("/act")
        self.assertEqual(self.agent.mode, "act")
        self.assertEqual(response, "Switched to ACT MODE. I will now execute the plan.")
        self.agent.api_handler.create_message.assert_not_called()

    @patch('cline.agent.agent.get_system_prompt')
    def test_plan_mode_uses_plan_prompt(self, mock_get_prompt):
        """Test that 'plan' mode uses the correct system prompt."""
        # Mock the context manager to prevent token counting during this test
        self.agent.context_manager = MagicMock()
        self.agent.context_manager.get_truncated_conversation_history.return_value = []

        self.agent.set_mode("plan")
        self.agent.api_handler.create_message.return_value = "<thinking>I am planning.</thinking>Some text."
        self.agent.step("Please plan a new feature.")
        
        # Check that get_system_prompt was called
        mock_get_prompt.assert_called_with(self.agent.tools)

    @patch('cline.agent.agent.get_system_prompt')
    def test_act_mode_uses_act_prompt(self, mock_get_prompt):
        """Test that 'act' mode uses the correct system prompt."""
        # Mock the context manager to prevent token counting during this test
        self.agent.context_manager = MagicMock()
        self.agent.context_manager.get_truncated_conversation_history.return_value = []
        
        self.agent.set_mode("act")
        self.agent.api_handler.create_message.return_value = "<thinking>I am acting.</thinking>Some text."
        self.agent.step("Execute the plan.")

        # Check that get_system_prompt was called
        mock_get_prompt.assert_called_with(self.agent.tools)

if __name__ == '__main__':
    unittest.main()
