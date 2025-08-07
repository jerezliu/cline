class MessageStateHandler:
    """Manages the conversation state for the Cline agent."""

    def __init__(self):
        """Initializes the MessageStateHandler."""
        self.cline_messages = []
        self.api_conversation_history = []

    def add_cline_message(self, message):
        """Adds a message to the Cline message history.

        Args:
            message: The message to add.
        """
        self.cline_messages.append(message)

    def add_api_conversation_history(self, message):
        """Adds a message to the API conversation history.

        Args:
            message: The message to add.
        """
        self.api_conversation_history.append(message)
