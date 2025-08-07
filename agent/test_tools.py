import unittest
from agent.tools import Tool, ToolParameter, get_tools

class TestTools(unittest.TestCase):
    """Tests for the tools module."""

    def test_tool_parameter_creation(self):
        """Tests the creation of a ToolParameter."""
        param = ToolParameter(name="path", param_type="string", description="The file path.", required=True)
        self.assertEqual(param.name, "path")
        self.assertEqual(param.param_type, "string")
        self.assertEqual(param.description, "The file path.")
        self.assertTrue(param.required)

    def test_tool_parameter_to_dict(self):
        """Tests the to_dict method of ToolParameter."""
        param = ToolParameter(name="path", param_type="string", description="The file path.", required=True)
        expected_dict = {
            "name": "path",
            "type": "string",
            "description": "The file path.",
            "required": True,
        }
        self.assertEqual(param.to_dict(), expected_dict)

    def test_tool_creation(self):
        """Tests the creation of a Tool."""
        param = ToolParameter(name="path", param_type="string", description="The file path.", required=True)
        tool = Tool(name="read_file", description="Reads a file.", parameters=[param])
        self.assertEqual(tool.name, "read_file")
        self.assertEqual(tool.description, "Reads a file.")
        self.assertEqual(len(tool.parameters), 1)
        self.assertEqual(tool.parameters[0], param)

    def test_tool_to_dict(self):
        """Tests the to_dict method of Tool."""
        param = ToolParameter(name="path", param_type="string", description="The file path.", required=True)
        tool = Tool(name="read_file", description="Reads a file.", parameters=[param])
        expected_dict = {
            "name": "read_file",
            "description": "Reads a file.",
            "parameters": [
                {
                    "name": "path",
                    "type": "string",
                    "description": "The file path.",
                    "required": True,
                }
            ],
        }
        self.assertEqual(tool.to_dict(), expected_dict)

    def test_get_tools(self):
        """Tests the get_tools function."""
        tools = get_tools()
        self.assertIsInstance(tools, list)
        self.assertGreater(len(tools), 0)
        for tool in tools:
            self.assertIsInstance(tool, Tool)

if __name__ == "__main__":
    unittest.main()
