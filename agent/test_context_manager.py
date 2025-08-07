import unittest
from unittest.mock import patch, MagicMock
from cline.agent.context_manager import ContextManager

class TestContextManager(unittest.TestCase):
    """Tests for the ContextManager class."""

    @patch('anthropic.Anthropic')
    def test_initialization(self, MockAnthropic):
        """Test that the ContextManager initializes correctly."""
        mock_client = MockAnthropic()
        context_manager = ContextManager(client=mock_client, model="claude-3-haiku-20240307")
        self.assertIsInstance(context_manager, ContextManager)

    @patch('anthropic.Anthropic')
    def test_get_truncated_conversation_history(self, MockAnthropic):
        """Test the get_truncated_conversation_history method."""
        mock_client = MockAnthropic()
        mock_client.messages.count_tokens.return_value = MagicMock(input_tokens=10)

        context_manager = ContextManager(client=mock_client, model="claude-3-haiku-20240307")
        conversation_history = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "Message 1"},
            {"role": "user", "content": "Message 2"},
            {"role": "user", "content": "Message 3"},
        ]
        
        truncated_history = context_manager.get_truncated_conversation_history(
            conversation_history,
            max_tokens=30
        )

        self.assertEqual(len(truncated_history), 3)
        self.assertEqual(truncated_history[0]["content"], "System prompt")
        self.assertEqual(truncated_history[1]["content"], "Message 2")
        self.assertEqual(truncated_history[2]["content"], "Message 3")

if __name__ == '__main__':
    unittest.main()
