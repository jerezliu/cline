import unittest
from unittest.mock import patch
from agent.prompts import get_system_prompt
from agent.tools import get_tools

class TestPrompts(unittest.TestCase):
    """Tests for the prompts module."""

    def setUp(self):
        """Set up the test case."""
        self.tools = get_tools()

    def test_get_system_prompt_with_browser(self):
        """Tests get_system_prompt with browser support enabled."""
        prompt = get_system_prompt(self.tools, supports_browser_use=True)
        self.assertIn("browser_action", prompt)

    def test_get_system_prompt_without_browser(self):
        """Tests get_system_prompt with browser support disabled."""
        prompt = get_system_prompt(self.tools, supports_browser_use=False)
        self.assertNotIn("browser_action", prompt)

    @patch('os.getcwd')
    @patch('os.name', 'test-os')
    @patch.dict('os.environ', {'SHELL': 'test-shell'})
    @patch('os.path.expanduser')
    def test_get_system_prompt_formats_correctly(self, mock_expanduser, mock_getcwd):
        """Tests that the prompt is formatted with the correct system info."""
        mock_getcwd.return_value = '/test/cwd'
        mock_expanduser.return_value = '/test/home'
        
        prompt = get_system_prompt(self.tools)
        
        self.assertIn("Current Working Directory: /test/cwd", prompt)
        self.assertIn("Operating System: test-os", prompt)
        self.assertIn("Default Shell: test-shell", prompt)
        self.assertIn("Home Directory: /test/home", prompt)

if __name__ == "__main__":
    unittest.main()
