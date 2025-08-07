import unittest
from unittest.mock import patch, mock_open, MagicMock
from cline.agent.tool_executor import ToolExecutor
from cline.agent.tools import get_tools

class TestToolExecutor(unittest.TestCase):
    """Tests for the ToolExecutor class."""

    def setUp(self):
        """Set up the test case."""
        self.tools = get_tools()
        self.executor = ToolExecutor(self.tools)

    def test_initialization(self):
        """Tests that the ToolExecutor initializes with the correct tools."""
        self.assertIn("read_file", self.executor._tools)
        self.assertIn("write_to_file", self.executor._tools)
        self.assertIn("list_files", self.executor._tools)
        self.assertIn("execute_command", self.executor._tools)
        self.assertIn("plan_mode_respond", self.executor._tools)

    def test_execute_tool_read_file(self):
        """Tests the read_file tool."""
        with patch("builtins.open", mock_open(read_data="file content")) as mock_file:
            result = self.executor.execute_tool("read_file", {"path": "test.txt"})
            self.assertEqual(result, "file content")
            mock_file.assert_called_once_with("test.txt", "r")

    def test_execute_tool_write_to_file(self):
        """Tests the write_to_file tool."""
        with patch("builtins.open", mock_open()) as mock_file:
            result = self.executor.execute_tool("write_to_file", {"path": "test.txt", "content": "new content"})
            self.assertEqual(result, "Successfully wrote to test.txt.")
            mock_file.assert_called_once_with("test.txt", "w")
            mock_file().write.assert_called_once_with("new content")

    def test_execute_tool_replace_in_file(self):
        """Tests the replace_in_file tool."""
        initial_content = "Hello world"
        diff = "------- SEARCH\nworld\n=======\nuniverse\n+++++++ REPLACE"
        with patch("builtins.open", mock_open(read_data=initial_content)) as mock_file:
            result = self.executor.execute_tool("replace_in_file", {"path": "test.txt", "diff": diff})
            self.assertEqual(result, "Successfully applied changes to test.txt.")
            mock_file().write.assert_called_once_with("Hello universe")

    @patch("os.walk")
    @patch("builtins.open", new_callable=mock_open, read_data="line with search_term")
    def test_execute_tool_search_files(self, mock_file, mock_walk):
        """Tests the search_files tool."""
        mock_walk.return_value = [
            ("/test", (), ("file1.txt", "file2.py")),
        ]
        # Test with regex
        result = self.executor.execute_tool("search_files", {"path": "/test", "regex": "search_term"})
        self.assertEqual(result, ["/test/file1.txt", "/test/file2.py"])

        # Test with file_pattern
        result = self.executor.execute_tool("search_files", {"path": "/test", "regex": "search_term", "file_pattern": "*.py"})
        self.assertEqual(result, ["/test/file2.py"])

    @patch("requests.get")
    def test_execute_tool_web_fetch(self, mock_get):
        """Tests the web_fetch tool."""
        mock_response = MagicMock()
        mock_response.text = "<html><body><p>Hello</p></body></html>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.executor.execute_tool("web_fetch", {"url": "http://example.com"})
        self.assertEqual(result, "Hello")

    def test_placeholder_tools(self):
        """Tests the placeholder tools."""
        placeholders = [
            "list_code_definition_names",
            "browser_action",
            "use_mcp_tool",
            "access_mcp_resource",
            "load_mcp_documentation",
            "new_task",
            "attempt_completion",
        ]
        for tool_name in placeholders:
            result = self.executor.execute_tool(tool_name, {})
            self.assertEqual(result, f"Tool '{tool_name}' is not implemented yet.")

    @patch("os.listdir")
    @patch("os.walk")
    def test_execute_tool_list_files(self, mock_walk, mock_listdir):
        """Tests the list_files tool."""
        # Test non-recursive
        mock_listdir.return_value = ["file1.txt", "dir1"]
        result = self.executor.execute_tool("list_files", {"path": ".", "recursive": False})
        self.assertEqual(result, ["file1.txt", "dir1"])
        
        # Test recursive
        mock_walk.return_value = [
            ("/test", ("sub",), ("file.txt",)),
            ("/test/sub", (), ("subfile.txt",))
        ]
        result = self.executor.execute_tool("list_files", {"path": "/test", "recursive": True})
        self.assertEqual(result, ["/test/file.txt", "/test/sub/subfile.txt"])

    @patch("subprocess.run")
    def test_execute_command(self, mock_run):
        """Tests the execute_command tool."""
        mock_run.return_value.stdout = "command output"
        mock_run.return_value.stderr = ""
        result = self.executor.execute_tool("execute_command", {"command": "ls"})
        self.assertEqual(result, "command output")

    def test_plan_mode_tool(self):
        """Tests the plan_mode_respond tool."""
        result = self.executor.execute_tool("plan_mode_respond", {"response": "test"})
        self.assertEqual(result, "test")

    def test_unknown_tool(self):
        """Tests calling an unknown tool."""
        result = self.executor.execute_tool("unknown_tool", {})
        self.assertEqual(result, "Tool 'unknown_tool' not found.")

if __name__ == "__main__":
    unittest.main()
