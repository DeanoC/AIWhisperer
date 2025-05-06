from ruamel.yaml import YAML
from io import StringIO

def handle_required_fields(yaml_content: str | dict, data: dict = None) -> tuple:
    """
    Ensure required fields are present with default values and optionally remove invalid fields.

   Args:
        yaml_content (str | dict): The input YAML content as a string or dictionary.
        data (dict): The input parameter dictionary and where results are also stored
            If data contains a 'preserve_extra_fields' key set to True, fields not in the schema will be preserved.
            Otherwise, only fields in the schema will be included in the output.

    Returns:
        The processed_yaml_content must be in the same format as the input (str | dict).
        tuple: (processed_yaml_content (str | dict), updated_result (dict))
   """
    # Initialize data if it's None
    if data is None:
        data = {
            "success": True,
            "steps": {},
            "logs": []
        }

    yaml = YAML()
    yaml.preserve_quotes = True

    # Ensure data has a logs key
    if "logs" not in data:
        data["logs"] = []

    try:
        # Parse the YAML content into a dictionary if it's a string
        if isinstance(yaml_content, str):
            parsed_yaml = yaml.load(yaml_content)
        elif isinstance(yaml_content, dict):
            parsed_yaml = yaml_content
        else:
            raise ValueError("Invalid input type. Expected a YAML string or dictionary.")

        # Check if we should preserve extra fields
        preserve_extra_fields = data.get("preserve_extra_fields", False)

        def process_fields(content, schema):
            if not isinstance(content, dict):
                return schema  # Replace invalid content with the default schema

            # Start with a copy of the original content if preserving extra fields, otherwise start with an empty dict
            result = content.copy() if preserve_extra_fields else {}

            # Add or update fields from the schema
            for key, default_value in schema.items():
                if isinstance(default_value, dict):  # Handle nested structures
                    if key in content and isinstance(content[key], dict):
                        # Process nested dictionaries
                        result[key] = process_fields(content[key], default_value)
                    else:
                        # Add missing nested structure
                        result[key] = process_fields({}, default_value)
                else:
                    # Use the content value if it exists and is valid, otherwise use default
                    if key in content and content[key] is not None and isinstance(content[key], type(default_value)):
                        result[key] = content[key]
                    else:
                        result[key] = default_value
            return result

        # Get the schema from the data dictionary
        schema = data.get("schema", {})

        # Process the fields based on the schema
        processed_yaml = process_fields(parsed_yaml, schema)

        data["logs"].append("Required fields processed.")

        # Return the same type as the input
        if isinstance(yaml_content, dict):
            return processed_yaml, data
        else:
            # Convert the processed dictionary back to a YAML string
            output = StringIO()
            yaml.dump(processed_yaml, output)
            return output.getvalue(), data
    except Exception as e:
        data["logs"].append(f"Error processing required fields: {e}")
        raise ValueError(f"Error processing required fields: {e}")
