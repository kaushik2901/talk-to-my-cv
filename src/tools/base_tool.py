from abc import ABC, abstractmethod
from typing import Self


class BaseTool(ABC):
    
    def __init__(self: Self, definition: dict):
        self.definition = definition

    @abstractmethod
    def function(self: Self, *args, **kwargs) -> dict:
        return { "arguments": [args, kwargs] }