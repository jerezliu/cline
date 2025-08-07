import unittest
import os
import platform
from unittest.mock import patch
from cline.agent.environment import EnvironmentManager

class TestEnvironmentManager(unittest.TestCase):
    """Tests for the EnvironmentManager class."""

    def setUp(self):
        """Set up the test case."""
        self.manager = EnvironmentManager()

    def test_get_cwd(self):
        """Tests the get_cwd method."""
        self.assertEqual(self.manager.get_cwd(), os.getcwd())

    def test_get_os(self):
        """Tests the get_os method."""
        self.assertEqual(self.manager.get_os(), platform.system())

    @patch.dict(os.environ, {"SHELL": "/bin/zsh"})
    def test_get_shell_with_env_var(self):
        """Tests the get_shell method when SHELL is set."""
        self.assertEqual(self.manager.get_shell(), "/bin/zsh")

    @patch.dict(os.environ, {}, clear=True)
    def test_get_shell_without_env_var(self):
        """Tests the get_shell method when SHELL is not set."""
        if "SHELL" in os.environ:
            del os.environ["SHELL"]
        self.assertEqual(self.manager.get_shell(), "Unknown")

    def test_get_context(self):
        """Tests the get_context method."""
        context = self.manager.get_context()
        self.assertIsInstance(context, dict)
        self.assertIn("cwd", context)
        self.assertIn("os", context)
        self.assertIn("shell", context)
        self.assertEqual(context["cwd"], os.getcwd())
        self.assertEqual(context["os"], platform.system())

    def test_get_environment_details(self):
        """Tests the get_environment_details method."""
        details = self.manager.get_environment_details("act")
        self.assertIn("<environment_details>", details)
        self.assertIn("</environment_details>", details)
        self.assertIn("ACT MODE", details)
        self.assertIn("Operating System", details)

if __name__ == "__main__":
    unittest.main()
