from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseParser(ABC):
    """Abstract Base Class untuk seluruh parser chat backup."""

    def __init__(self, file_path: str):
        self.file_path = file_path

    @abstractmethod
    def parse(self) -> Dict[str, Any]:
        """
        Wajib mengembalikan dictionary dengan struktur standar:
        {
            "title": str,
            "created_at": str,
            "messages": [
                {
                    "role": "user" | "assistant" | "system",
                    "content": str,
                    "timestamp": str
                }
            ]
        }
        """
        pass

    @abstractmethod
    def validate(self) -> bool:
        """Cek apakah format file valid dan bisa diproses."""
        pass