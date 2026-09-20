from abc import ABC, abstractmethod
from typing import Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class ModelGateway(ABC):
    """Provider-agnostic interface for structured LLM output.

    Agents call this instead of a provider SDK directly, so adding/swapping
    providers (Anthropic, Google, xAI, self-hosted, ...) never touches agent logic.
    """

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Provider-qualified id (e.g. 'openai:gpt-5.5') for point-in-time record-keeping."""

    @abstractmethod
    def generate_structured(
        self, *, system: str, user: str, response_model: Type[T]
    ) -> T:
        ...
