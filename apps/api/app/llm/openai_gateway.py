from typing import Type, TypeVar

from openai import OpenAI
from pydantic import BaseModel

from app.llm.gateway import ModelGateway

T = TypeVar("T", bound=BaseModel)


class OpenAIGateway(ModelGateway):
    def __init__(self, api_key: str, model: str):
        self._client = OpenAI(api_key=api_key)
        self._model = model

    @property
    def model_id(self) -> str:
        return f"openai:{self._model}"

    def generate_structured(
        self, *, system: str, user: str, response_model: Type[T]
    ) -> T:
        response = self._client.responses.parse(
            model=self._model,
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            text_format=response_model,
        )
        return response.output_parsed
