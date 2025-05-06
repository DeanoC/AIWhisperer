import pytest
from src.postprocessing.pipeline import PostprocessingPipeline
from src.postprocessing.scripted_steps.normalize_indentation import normalize_indentation
from src.postprocessing.scripted_steps.handle_required_fields import handle_required_fields
from src.postprocessing.scripted_steps.validate_syntax import validate_syntax

SCHEMA = {
    "required_field_1": "default_value_1",
    "required_field_2": "default_value_2",
    "nested_field": {
        "nested_required_1": "nested_default_1"
    }
}

@pytest.mark.parametrize("input_yaml, expected_yaml", [
    # Case: All steps applied successfully
    (
        "key:\n\t  subkey: value\n",
        "key:\n  subkey: value\nrequired_field_1: default_value_1\nrequired_field_2: default_value_2\nnested_field:\n  nested_required_1: nested_default_1\n"
    ),
    # Case: Missing required fields
    (
        "key: value\n",
        "key: value\nrequired_field_1: default_value_1\nrequired_field_2: default_value_2\nnested_field:\n  nested_required_1: nested_default_1\n"
    ),
    # Case: Invalid syntax
    (
        "key value\n",
        None  # Should raise a ValueError
    ),
    # Case: Empty YAML
    (
        "",
        "required_field_1: default_value_1\nrequired_field_2: default_value_2\nnested_field:\n  nested_required_1: nested_default_1\n"
    ),
])
def test_postprocessing_pipeline(input_yaml, expected_yaml):
    pipeline = PostprocessingPipeline()
    pipeline.add_step(normalize_indentation)
    pipeline.add_step(validate_syntax)
    pipeline.add_step(lambda content, data: handle_required_fields(content, {**data, "schema": SCHEMA, "preserve_extra_fields": True}))

    if expected_yaml is None:
        # For invalid syntax, any step in the pipeline might raise a ValueError
        # (either normalize_indentation or validate_syntax)
        with pytest.raises(ValueError):
            pipeline.process(input_yaml)
    else:
        output_yaml, _ = pipeline.process(input_yaml)
        assert output_yaml.strip() == expected_yaml.strip()
