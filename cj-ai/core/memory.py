from dataclasses import dataclass, field
from config import MAX_HISTORY


@dataclass
class Message:
    role: str   # 'user' or 'assistant'
    content: str


class SessionMemory:
    """Keeps recent conversation turns in memory for the current session."""

    def __init__(self, max_size: int = MAX_HISTORY):
        self.max_size = max_size
        self._history: list[Message] = []

    def add(self, role: str, content: str):
        self._history.append(Message(role=role, content=content))
        if len(self._history) > self.max_size:
            self._history.pop(0)

    def get_history(self) -> list[Message]:
        return list(self._history)

    def last_user_message(self) -> str | None:
        for msg in reversed(self._history):
            if msg.role == "user":
                return msg.content
        return None

    def clear(self):
        self._history.clear()

    def __len__(self) -> int:
        return len(self._history)
