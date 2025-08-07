import unittest
from unittest.mock import patch, MagicMock
from cline.agent.api_handler import ApiHandler

class TestApiHandler(unittest.TestCase):
    """Tests for the ApiHandler class."""

    @patch('anthropic.Anthropic')
    def test_initialization(self, MockAnthropic):
        """Test that the ApiHandler initializes correctly."""
        api_handler = ApiHandler(api_configuration={"api_key": "test_key", "model": "claude-3-opus-20240229"})
        self.assertIsInstance(api_handler, ApiHandler)
        MockAnthropic.assert_called_once_with(api_key="test_key")

    @patch('anthropic.Anthropic')
    def test_create_message(self, MockAnthropic):
        """Test the create_message method."""
        mock_anthropic_instance = MockAnthropic.return_value
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Hello, world!")]
        mock_anthropic_instance.messages.create.return_value = mock_response

        api_handler = ApiHandler(api_configuration={"api_key": "test_key", "model": "claude-3-opus-20240229"})
        conversation_history = [
            {"role": "user", "content": "Hello"}
        ]
        
        response = api_handler.create_message("system prompt", conversation_history)

        self.assertEqual(response, mock_response)
        mock_anthropic_instance.messages.create.assert_called_once_with(
            model="claude-3-opus-20240229",
            max_tokens=4096,
            messages=conversation_history,
            system="system prompt",
        )

if __name__ == '__main__':
    unittest.main()
