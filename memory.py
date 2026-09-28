from collections import deque


class ConversationMemory:
    def __init__(self, max_messages=10):
        self.max_messages = max_messages
        self.messages = deque(maxlen=max_messages)

    def add_user_message(self, text):
        self.messages.append({"role": "user", "content": text})

    def add_assistant_message(self, text):
        self.messages.append({"role": "assistant", "content": text})

    def get_recent(self, n=10):
        return list(self.messages)[-n:]

    def format_for_rewrite(self):
        lines = []
        for msg in self.messages:
            lines.append(f"{msg['role'].capitalize()}: {msg['content']}")
        return "\n".join(lines)

    def clear(self):
        self.messages.clear()
