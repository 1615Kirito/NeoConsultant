import json
from typing import TypeVar

from pydantic import BaseModel
from langchain.chat_models import init_chat_model

from finsight_mcp.config import settings


T = TypeVar(
    "T",
    bound=BaseModel,
)


class llm:

    def __init__(
        self,
        max_tokens: int = 4096,
    ):
        self.model = init_chat_model(
            settings.model_name,
            model_provider="openai",
            base_url="https://api.deepseek.com",
            api_key=settings.deepseek_api_key,
            temperature=0,
            max_tokens=max_tokens,
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