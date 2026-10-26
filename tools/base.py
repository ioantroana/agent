from abc import ABC, abstractmethod
from typing import ClassVar

from anthropic.types import ToolParam
from pydantic import BaseModel

class Tool[InputT: BaseModel](ABC):
    """Base class for every tool. InputT is the Pydantic class for the tool's input."""

    name: ClassVar[str]
    description: ClassVar[str]
    input_model: ClassVar[type[BaseModel]]
    needs_review: ClassVar[bool] = False  # True for anything that changes files

    def definition(self) -> ToolParam:
        # The input schema is generated from the Pydantic class, so it can't drift from the code
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_model.model_json_schema(),
        }

    def parse_input(self, raw: object) -> InputT:
        # Raises pydantic.ValidationError if the model sent the wrong shape
        return self.input_model.model_validate(raw)  # type: ignore[return-value]

    @abstractmethod
    def run(self, args: InputT) -> str: ...
