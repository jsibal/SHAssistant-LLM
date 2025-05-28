from typing import Optional

from langchain_core.messages import BaseMessage, HumanMessage


def filter_messages(messages: list[BaseMessage], n: Optional[int] = None) -> list[BaseMessage]:
    if not messages:
        return []
    if n is None:
        return messages

    current_n = 0
    filtered_messages = []
    for m in reversed(messages):
        filtered_messages.append(m)

        if isinstance(m, HumanMessage):
            current_n += 1
        if current_n >= n:
            break

    return list(reversed(filtered_messages))