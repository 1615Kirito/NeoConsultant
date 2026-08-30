import json
from typing import TypeVar

from pydantic import BaseModel
from langchain.chat_models import init_chat_model


T = TypeVar(
    "T",
    bound=BaseModel,
)


class llm:

    def __init__(
        self,
        model_name: str = "gpt-5.4-mini",
    ):
        self.model = init_chat_model(
            model_name,
            temperature=0,
        )

    async def generate(
        self,
        output_schema: type[T],
        instructions: str,
        inputs: dict,
        task_name: str,
    ) -> T:
        """
        Generate structured output using an LLM.

        Parameters
        ----------
        output_schema:
            Pydantic schema defining the expected output.

        instructions:
            System instructions for the agent.

        inputs:
            Input data provided to the agent.

        task_name:
            Name of the generation task, mainly useful
            for logging/debugging.

        Returns
        -------
        T
            Validated Pydantic model.
        """

        structured_model = (
            self.model.with_structured_output(
                output_schema
            )
        )

        messages = [
            (
                "system",
                instructions,
            ),
            (
                "human",
                json.dumps(
                    inputs,
                    indent=2,
                    default=str,
                ),
            ),
        ]

        result = await structured_model.ainvoke(
            messages
        )

        return result