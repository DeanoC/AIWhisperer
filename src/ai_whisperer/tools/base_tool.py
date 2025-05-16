from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class AITool(ABC):
    """
    Abstract base class for all AI-usable tools in the AIWhisperer project.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        A unique, machine-readable identifier for the tool.
        e.g., "read_file", "execute_python_code"
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """
        A concise, human-readable description of what the tool does.
        e.g., "Reads the content of a specified text file."
        """
        pass

    @property
    @abstractmethod
    def parameters_schema(self) -> Dict[str, Any]:
        """
        A JSON schema object defining the input parameters for the tool.
        This schema is used for validation and for generating the Openrouter tool definition.
        """
        pass

    @property
    def category(self) -> Optional[str]:
        """
        A broad category for the tool (e.g., "File System", "Code Execution", "Data Analysis", "Communication").
        Returns None if not categorized.
        """
        return None

    @property
    def tags(self) -> List[str]:
        """
        A list of keywords or tags describing the tool's capabilities or domain.
        e.g., ["file_io", "read", "text"], ["python", "scripting"]
        Returns an empty list if no tags are applicable.
        """
        return []

    def get_openrouter_tool_definition(self) -> Dict[str, Any]:
        """
        Generates the tool definition in a format compatible with the Openrouter API
        (specifically, the OpenAI function calling format).
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema
            }
        }

    @abstractmethod
    def get_ai_prompt_instructions(self) -> str:
        """
        Generates clear and concise instructions for the AI model on how and when
        to use the tool, including details about its purpose, parameters,
        and expected output.
        """
        pass

    @abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        """
        The core logic for the tool's operation.
        It receives parameters as keyword arguments, validated against parameters_schema.

        Args:
            **kwargs: The parameters for the tool, matching the parameters_schema.

        Returns:
            The output of the tool's execution. This can be of any type
            (e.g., string, dictionary, list) relevant to the tool's function.
            The output should be serializable if it needs to be passed back to the AI.
        """
        pass