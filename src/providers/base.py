from abc import ABC, abstractmethod
from typing import AsyncGenerator


class BaseProvider(ABC):
    @abstractmethod
    async def generate_stream(
        self,
        model: str,
        messages: list[dict],
    ) -> AsyncGenerator[str, None]:
        """
        Gera uma resposta em streaming.

        Deve retornar pequenos pedaços (chunks) da resposta.
        """
        pass