import re


def clean_backtick_wrapper(content: str | dict, data: dict) -> tuple:
    """
    Removes code block wrappers (e.g., ```json, ```yaml) from the input data.

    Args:
        content (str | dict): The input content as a string or dictionary.
        data (dict): The input parameter dictionary and where results are also stored

    Returns:
        tuple: A tuple containing:
            - processed_content (str | dict): The content with backtick wrappers removed.
              Must be in the same format as the input.
            - updated_data (dict): The updated data dictionary with processing logs.

    Note:
        This function follows the required signature for all scripted processing steps:
        - Takes (content, data) as input
        - Returns a tuple of (processed_content, updated_data)
        - The parameter and return types are fixed and cannot be changed:
          * content: str | dict
          * data: dict
          * return: tuple[str | dict, dict]
        - Preserves the input format (str or dict) in the output

    Example:
        >>> content_json = "```json\\n{\\"task\\": \\"example\\"}\\n```"
        >>> data_json = {"logs": []}
        >>> output_json, output_data_json = clean_backtick_wrapper(content_json, data_json)
        >>> assert output_json == '{\\"task\\": \\"example\\"}\\n'
        >>> assert output_data_json == data_json

        >>> content_yaml = "```yaml\\ntask: example\\n```"
        >>> data_yaml = {"logs": []}
        >>> output_yaml, output_data_yaml = clean_backtick_wrapper(content_yaml, data_yaml)
        >>> assert output_yaml == "task: example\\n"
        >>> assert output_data_yaml == data_yaml
    """
    # If content is a dictionary, return it as is
    if isinstance(content, dict):
        if "logs" in data:
            data["logs"].append("Input is a dictionary, no backtick wrappers to remove.")
        return (content, data)

    # Log the original content for debugging
    if "logs" in data:
        data["logs"].append(f"Original content starts with: {content[:20]}")

    # Remove the outer code block wrappers (``` with optional language specifier at the start and ``` at the end)
    # This regex makes the newlines after the opening and before the closing backticks optional.
    if not content:
        # Log the cleaning step for empty content
        if "logs" in data:
            data["logs"].append(f"Removed all backticks. Cleaned content starts with: ")
        return (content, data)

    cleaned_content = re.sub(r"^```[a-zA-Z]*\n?(.*)\n?```$", r"\1", content, flags=re.DOTALL)

    # Log the cleaning step
    if "logs" in data:
        data["logs"].append(f"Removed all backticks. Cleaned content starts with: {cleaned_content[:20]}")

    return (cleaned_content, data)
