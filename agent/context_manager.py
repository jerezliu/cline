import anthropic


class ContextManager:
    """Manages the context window for the Cline agent."""

    def __init__(self, client, model: str):
        """Initializes the ContextManager.

        Args:
            client: An instance of anthropic.Anthropic.
            model (str): The model name to use for token counting.
        """
        self.client = client
        self.model = model

    def get_truncated_conversation_history(self, conversation_history, max_tokens):
        """Truncates the conversation history to fit within the specified token limit.

        This method preserves the system prompt (the first message) and truncates
        from the middle of the conversation history to stay within the token limit.

        Args:
            conversation_history (list[dict]): The conversation history, where each
                dictionary represents a message with 'role' and 'content' keys.
            max_tokens (int): The maximum number of tokens allowed.

        Returns:
            list[dict]: The truncated conversation history.
        """
        if not conversation_history:
            return []

        # The first message is always the system prompt and must be kept.
        system_prompt = conversation_history[0]
        messages_to_truncate = conversation_history[1:]

        # Calculate token count for the system prompt.
        system_prompt_tokens = self.client.messages.count_tokens(
            model=self.model,
            messages=[system_prompt]
        ).input_tokens
        current_tokens = system_prompt_tokens
        
        truncated_messages = []
        
        # Iterate backwards from the most recent messages.
        for message in reversed(messages_to_truncate):
            message_tokens = self.client.messages.count_tokens(
                model=self.model,
                messages=[message]
            ).input_tokens
            if current_tokens + message_tokens > max_tokens:
                break
            current_tokens += message_tokens
            truncated_messages.insert(0, message)

        return [system_prompt] + truncated_messages
