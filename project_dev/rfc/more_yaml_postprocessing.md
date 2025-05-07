# Context

Our current prompts enforce strict formatting rules to ensure the AI generates YAML outputs that meet our requirements. While this approach works, it places unnecessary complexity on the AI and increases the risk of formatting errors.

We already have a postprocessing system in place that can modify and clean up YAML outputs after they are generated. By extending this system, we can offload more formatting and cleanup tasks from the AI to our postprocessing pipeline.

## Goals

1. **Reduce Prompt Complexity:** Remove strict YAML formatting rules from our prompts, allowing the AI to focus on generating accurate content rather than adhering to rigid formatting requirements.
2. **Extend Postprocessing:** Add new postprocessing steps to handle YAML cleanup and formatting tasks, ensuring the final output meets our standards.
3. **Improve Robustness:** Ensure that the postprocessing pipeline can handle common formatting issues (e.g., inconsistent indentation, missing fields, invalid YAML syntax) and correct them automatically.
4. **Maintain Test-Driven Development:** Use a test-first approach to ensure all new postprocessing steps are thoroughly validated.

## Requirements

1. **New Postprocessing Steps:**
   - Implement additional scripted steps in the `src/postprocessing/scripted_steps` folder to handle YAML cleanup tasks, such as:
     - Normalizing indentation.
     - Ensuring required fields are present with default values if missing.
     - Removing unnecessary or invalid fields.
     - Validating and correcting YAML syntax.
   - Try to create steps that do a single part of the cleanup instead of a large single step having several concerns
   - Integrate these steps into the existing `PostprocessingPipeline` in `src/postprocessing/pipeline.py`.

2. **Prompt Updates:**
   - Remove strict YAML formatting rules from the prompts in the `prompts` folder (e.g., `orchestrator_default.md`, `subtask_generator_default.md`).
   - Focus prompts on content generation rather than formatting.

3. **Testing:**
   - Write unit tests for each new postprocessing step to ensure they handle a variety of edge cases.
   - Add integration tests for the updated pipeline to verify that the final YAML output meets all requirements.

4. **Documentation:**
   - Update the documentation in the `docs` folder to reflect the new postprocessing capabilities.
   - Provide examples of how the prompts can be simplified as a result of these changes.

## Benefits

- Simplifies prompt design, making it easier to maintain and extend.
- Reduces the likelihood of formatting errors in AI-generated outputs.
- Improves the overall robustness and reliability of the system.
