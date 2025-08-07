import anthropic


class ApiHandler:
    """Handles communication with AI providers."""

    def __init__(self, api_configuration):
        """Initializes the ApiHandler.

        Args:
            api_configuration: The API configuration.
        """
        self.api_configuration = api_configuration
        self.client = anthropic.Anthropic(api_key=self.api_configuration['api_key'])

    def create_message(self, system_prompt, conversation_history):
        """Creates a message using the specified AI provider.

        Args:
            system_prompt: The system prompt.
            conversation_history: The conversation history.

        Returns:
            The full API response object.
        """
        response = self.client.messages.create(
            model=self.api_configuration['model'],
            system=system_prompt,
            messages=conversation_history,
            max_tokens=4096,
        )
        return response
