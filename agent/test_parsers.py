import unittest
from cline.agent.parsers import parse_assistant_message, TextContent, ToolUse

class TestParsers(unittest.TestCase):
    """Tests for the parsers module."""

    def test_parse_assistant_message_with_text(self):
        """Test parsing a message with only text."""
        message_content = "Hello, world!"
        parsed_message = parse_assistant_message(message_content)
        self.assertEqual(len(parsed_message), 1)
        self.assertIsInstance(parsed_message[0], TextContent)
        self.assertEqual(parsed_message[0].content, "Hello, world!")

    def test_parse_assistant_message_with_tool_code(self):
        """Test parsing a message with a tool code block."""
        message_content = """
<test_tool>
<param1>value1</param1>
</test_tool>
"""
        parsed_message = parse_assistant_message(message_content)
        self.assertEqual(len(parsed_message), 1)
        self.assertIsInstance(parsed_message[0], ToolUse)
        self.assertEqual(parsed_message[0].name, "test_tool")
        self.assertEqual(parsed_message[0].params, {"param1": "value1"})

    def test_parse_assistant_message_with_no_tool_code(self):
        """Test parsing a message with no tool code."""
        message_content = "Hello, world!"
        parsed_message = parse_assistant_message(message_content)
        self.assertEqual(len(parsed_message), 1)
        self.assertIsInstance(parsed_message[0], TextContent)
        self.assertEqual(parsed_message[0].content, "Hello, world!")

if __name__ == '__main__':
    unittest.main()
