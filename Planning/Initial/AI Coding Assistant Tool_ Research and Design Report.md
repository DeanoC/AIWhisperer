# AI Coding Assistant Tool: Research and Design Report

## 1. Introduction

This report summarizes the research and design process undertaken to plan a tool aimed at improving collaboration with AI code assistants. The goal, as outlined by the user, is to address challenges related to the ambiguity of natural language specifications and the need for better task decomposition for AI agents. The proposed solution involves a tool that leverages hierarchical AI models (accessed via OpenRouter) to iteratively translate a natural language goal into a precise, AI-consumable specification format, manage task execution, and incorporate feedback loops for refinement.

This report covers:

* Research findings on relevant concepts: formal specification methods, structured prompting, Domain Specific Languages (DSLs), handling natural language ambiguity, OpenRouter capabilities, and hierarchical AI agent architectures.
* The proposed design for an AI-friendly specification format (YAML-based).
* The proposed iterative tool architecture, including planner/executor roles, validation, and refinement loops (both pre- and post-execution).

The aim is to provide sufficient information to inform the subsequent development planning phase.

## 2. Research Findings

### 2.1 Formal Methods for Software Specification

Formal methods represent a collection of mathematically rigorous techniques applied throughout the software and hardware development lifecycle, encompassing specification, development, analysis, and verification. The primary motivation behind employing these methods is to enhance the reliability and robustness of the final system, drawing parallels with other engineering disciplines where mathematical analysis is crucial for ensuring design integrity. These methods are built upon fundamental concepts from theoretical computer science, including logic calculi, formal languages, automata theory, control theory, program semantics, type systems, and type theory.

One key application of formal methods is in **formal specification**. This involves creating a precise, unambiguous description of the system to be developed using a formal language. Such a specification serves multiple purposes. It can help uncover and resolve ambiguities present in informal requirements documentation. Furthermore, it provides a clear reference point for engineers during the development process. The need for formal ways to describe systems, particularly programming language syntax, was recognized early on, leading to notations like Backus-Naur Form (BNF).

Beyond specification, formal methods are utilized in **program synthesis**, which aims to automatically generate program code that adheres to a given formal specification. This often involves searching through a vast space of potential programs, making efficient search algorithms a critical area of research.

Another significant application is **formal verification**. This process uses software tools to mathematically prove specific properties of a formal specification or to demonstrate that a formal model of a system implementation correctly satisfies its specification. Verification can take several forms. Human-directed proofs involve constructing arguments similar to mathematical proofs, focusing on clarity and understanding, though they can be susceptible to subtle errors due to the inherent ambiguity of natural language. Automated techniques offer greater rigor and include automated theorem proving (generating proofs from axioms and inference rules), model checking (exhaustively exploring all possible system states to verify properties), and abstract interpretation (analyzing an over-approximation of system behavior). While automated methods provide higher mathematical certainty, challenges like verifying the verifier itself remain.

**Relevance:** The principles of formal specification – precision, lack of ambiguity, mathematical rigor – are directly relevant to creating AI-consumable task descriptions. While a full formal specification language might be too complex for initial LLM generation, adopting structured formats inspired by formal methods (like the proposed YAML schema) can significantly reduce ambiguity compared to pure natural language.

Source: [https://en.wikipedia.org/wiki/Formal_methods](https://en.wikipedia.org/wiki/Formal_methods)

### 2.2 Structured Prompting Techniques for LLMs

Interacting effectively with Large Language Models (LLMs) often involves choosing between conversational and structured prompting approaches. Conversational prompting is intuitive, allowing users to interact with the AI using natural language, much like a dialogue. This method is accessible, user-friendly, and allows for dynamic refinement based on context. However, it can lead to inconsistent results, varying quality, and difficulties in encoding specialized knowledge or enforcing strict constraints.

Structured prompting, conversely, involves carefully crafting prompts with explicit instructions, examples, constraints, and potentially a defined format (like JSON or XML). This approach treats the prompt more like a program or script, guiding the LLM's behavior more predictably. By encoding expertise and workflow logic into the prompt, structured prompting aims to achieve higher reliability, consistency, and the ability to handle complex tasks by breaking them down. It allows for better control over the output format and ensures that specific requirements are met. While requiring more upfront effort to design the prompt structure, this method is better suited for specialized, repeatable tasks where precision and predictability are paramount. Techniques include using delimiters to separate parts of the prompt, specifying output formats, providing few-shot examples, and breaking down complex tasks into steps (chain-of-thought). A hybrid approach, combining structured elements within a conversational flow, can also be effective, leveraging the strengths of both methods.

**Relevance:** The proposed YAML specification format directly incorporates structured prompting principles within the `instructions`, `constraints`, and `validation_criteria` fields for each step. This allows detailed, precise guidance to be given to the executor agents, reducing reliance on ambiguous conversational instructions and improving the predictability and reliability of their outputs.

Source: [https://promptengineering.org/a-guide-to-conversational-and-structured-prompting/](https://promptengineering.org/a-guide-to-conversational-and-structured-prompting/)

### 2.3 Domain Specific Languages (DSLs) for Task Definition

A Domain-Specific Language (DSL) is a computer language tailored to a particular application domain, contrasting with General-Purpose Languages (GPLs) like Python or Java which are broadly applicable. DSLs aim to express problems and solutions within their specific domain more clearly and concisely than a GPL might allow. Examples range from widely used ones like HTML (web pages) and SQL (database queries) to highly specialized ones used within specific software or business areas (e.g., finance, simulations).

DSLs can be textual (like regular expressions in `grep` or configuration files), graphical (like UML diagrams or specific modeling tools), or embedded within a host GPL (often implemented as libraries or using metaprogramming features). External DSLs have their own parsers and interpreters/compilers (e.g., AWK, TeX), while internal/embedded DSLs leverage the host language's syntax and infrastructure.

The key advantage of a DSL is increased expressiveness and productivity within its target domain. It allows domain experts, who may not be expert programmers, to define or manipulate systems using familiar terminology and concepts. This can lead to clearer specifications, reduced errors, and easier validation. However, DSLs come with the cost of design, implementation, and maintenance. There's also a learning curve for users, and the DSL might lack the flexibility or tooling available for GPLs.

In the context of AI, DSLs can serve as a precise intermediate representation between potentially ambiguous natural language instructions and the code or actions an AI needs to generate or perform. By defining a structured language specific to the task domain (e.g., UI generation, data transformation, API calls), a higher-level AI could translate natural language into this DSL, which a lower-level AI could then reliably execute. This aligns with the goal of providing more precise, AI-consumable specifications.

**Relevance:** While creating a full DSL is a significant undertaking, the proposed YAML format acts as a *structured configuration* or a *simple textual DSL* for defining the AI workflow. It provides specific keywords (`step_id`, `depends_on`, `agent_spec`, `instructions`, etc.) with defined semantics, offering more structure than free-form text but less complexity than a fully parsed language. It serves as a practical intermediate step towards a more formal, AI-specific representation.

Source: [https://en.wikipedia.org/wiki/Domain-specific_language](https://en.wikipedia.org/wiki/Domain-specific_language)

### 2.4 Handling Ambiguity in Natural Language for AI Instructions

Natural language is inherently ambiguous, meaning words, phrases, or sentences can have multiple interpretations. This poses a significant challenge for AI systems, particularly Large Language Models (LLMs), which rely on precise instructions to generate desired outputs. Unlike humans who use context, intuition, and world knowledge to disambiguate, AI requires explicit strategies.

Several types of ambiguity exist:

* **Lexical Ambiguity:** A single word has multiple meanings (e.g., "bat" - animal vs. sports equipment).
* **Syntactic (Structural) Ambiguity:** Sentence structure allows multiple grammatical interpretations (e.g., "I saw the man with the telescope" - who has the telescope?).
* **Semantic Ambiguity:** The meaning of a sentence is unclear due to word combinations, even if grammatically correct (e.g., "Visiting relatives can be annoying" - the act of visiting or the relatives themselves?).
* **Pragmatic Ambiguity:** Meaning depends on context, speaker intent, or tone (e.g., "Can you open the window?" - question vs. request).
* **Referential Ambiguity:** Pronouns or references are unclear about what they point to (e.g., "Alice told Jane that *she* would win" - who is *she*?).
* **Ellipsis Ambiguity:** Omitted parts of a sentence create uncertainty (e.g., "John likes apples, and Mary does too" - does Mary like apples or something else?).

Addressing ambiguity in AI instructions, especially for LLMs, involves several techniques:

* **Contextual Analysis:** Analyzing surrounding words, sentences, or the broader conversation/document to infer the most likely meaning.
* **Word Sense Disambiguation (WSD):** Algorithms specifically designed to identify the correct meaning of a word in context.
* **Parsing and Syntactic Analysis:** Breaking down sentence structure to identify and potentially resolve structural ambiguities.
* **Coreference Resolution:** Identifying all expressions that refer to the same entity in a text.
* **Discourse and Pragmatic Modeling:** Attempting to model speaker intent, dialogue state, and social context.
* **Clarification Dialogues:** Designing the AI to ask clarifying questions when ambiguity is detected.
* **Structured Input/Formats:** Using more structured inputs like templates, forms, or DSLs (as researched previously) inherently reduces ambiguity compared to free-form natural language.
* **Machine Learning Models:** Modern LLMs (like BERT, GPT) are trained on vast datasets and implicitly learn to handle some ambiguity through contextual understanding, but they are not perfect and benefit from explicit disambiguation strategies or clearer prompting.

**Relevance:** The proposed tool directly addresses ambiguity by translating natural language into the structured YAML format. The inclusion of specific fields like `constraints` and `validation_criteria`, along with the pre-execution understanding check loop, further forces clarification and reduces the chances of misinterpretation by the executor agents.

Source: [https://www.geeksforgeeks.org/ambiguity-in-nlp-and-how-to-address-them/](https://www.geeksforgeeks.org/ambiguity-in-nlp-and-how-to-address-them/)

### 2.5 OpenRouter Capabilities (API, Models, Pricing)

OpenRouter positions itself as a unified interface for accessing a wide variety of Large Language Models (LLMs) through a single API endpoint. Key aspects relevant to the proposed tool include:

* **Unified API:** OpenRouter provides a standardized API, largely compatible with the OpenAI API format, allowing developers to switch between different models from various providers (OpenAI, Anthropic, Google, Meta, Mistral, open-source models, etc.) with minimal code changes. This simplifies integration and experimentation with different models.
* **Extensive Model Selection:** The platform boasts access to over 300 model endpoints (as of May 2025), including various versions of popular models like GPT, Claude, Gemini, Llama, Phi, Qwen, as well as specialized or fine-tuned models. The model list page ([https://openrouter.ai/models](https://openrouter.ai/models)) allows filtering by capabilities (text, image, file input), context length, pricing, series (e.g., GPT, Claude), and categories (e.g., programming, roleplay).
* **Variable Pricing:** Pricing is model-specific and typically charged per million input tokens and per million output tokens. Costs vary significantly between models, reflecting differences in capability, speed, and provider costs. OpenRouter displays pricing transparently on its model list page. Some models are offered for free (often with lower rate limits). This pay-as-you-go structure allows for cost optimization by selecting the most appropriate model for a given task's complexity and budget.
* **Tokenization Differences:** The documentation notes that different models use different tokenizers (e.g., multi-character chunks vs. per-character). This means token counts and associated costs can vary even for identical input/output text across different models. The API response includes usage details for accurate cost tracking.
* **Features:** Beyond basic model access, OpenRouter offers features like model routing (automatic fallback), provider routing, prompt caching, structured outputs, tool calling, image/PDF processing, web search integration, and uptime optimization, although details would require further investigation into specific documentation sections.

**Relevance:** OpenRouter appears well-suited for the proposed tool's requirement of accessing diverse models with varying cost/performance profiles through a single interface, facilitating the hierarchical approach where different models might be used for planning versus execution or validation. The `model_preference` field in the YAML spec allows leveraging this flexibility directly.

Sources:

* [https://openrouter.ai/docs/models](https://openrouter.ai/docs/models) (Accessed via direct navigation)
* [https://openrouter.ai/models](https://openrouter.ai/models) (Accessed via browser click from docs)

### 2.6 Hierarchical AI Agent Architectures & LLMs

Hierarchical structures are a common approach for building more complex and capable AI agent systems, particularly those involving LLMs. Instead of a single monolithic agent trying to handle everything, tasks are broken down and delegated among specialized agents operating at different levels.

**Common Patterns:**

* **Supervisor/Worker (Router):** A higher-level agent (supervisor or router) analyzes an incoming task or query and decides which specialized lower-level agent (worker) is best suited to handle it or a specific sub-task. The supervisor might use the LLM's reasoning capabilities, often combined with structured output or tool calling, to select the appropriate worker or next step from a predefined set. Frameworks like LangGraph explicitly support this pattern, often representing agents as nodes in a graph with a supervisor node directing the flow.
* **Planner/Executor:** A planning agent breaks down a complex goal into a sequence of smaller, manageable steps. These steps are then passed to one or more executor agents, which might be specialized in specific actions (e.g., code generation, API calls, database queries). The planner might use an LLM's ability to reason and generate multi-step plans.
* **ReAct (Reason + Act):** While not strictly hierarchical in the supervisor/worker sense, ReAct is a common pattern for tool-using agents. The agent iteratively reasons (Thought), decides on an action (Act - often calling a tool), and observes the result, repeating until the task is complete. This iterative process can be seen as a form of single-agent planning and execution cycle.

**Frameworks and Concepts (e.g., LangGraph):**

* **Agents as Control Flow:** Agents use LLMs to decide the application's control flow, moving beyond fixed sequences like simple RAG.
* **Tool Calling:** Essential for agents to interact with external systems or perform specific functions. LLMs are trained to generate the correct inputs for predefined tools (functions, APIs).
* **Memory:** Crucial for agents to maintain context across multiple steps or interactions. This can be short-term (within a single task execution) or long-term (across multiple sessions). Frameworks often provide mechanisms for managing agent state and persisting it (checkpointers).
* **Structured Output:** Ensuring the LLM's decisions (e.g., which tool to call, which route to take) are in a predictable format.
* **Subgraphs:** In complex multi-agent systems, subgraphs allow encapsulating the logic and state of individual agents or teams, facilitating modularity and hierarchical organization.
* **Reflection/Self-Correction:** Agents can evaluate their own work or the output of other agents, identify errors or shortcomings, and trigger corrective actions or refinement loops. This can involve using an LLM to critique an output or using deterministic checks (like code compilation errors).

**Relevance:** The proposed architecture directly implements a hierarchical Planner/Executor pattern, leveraging OpenRouter to potentially use different LLMs for each role. The iterative refinement loops incorporate reflection and self-correction principles.

Source: [https://langchain-ai.github.io/langgraph/concepts/agentic_concepts/](https://langchain-ai.github.io/langgraph/concepts/agentic_concepts/)

## 3. Design: AI-Friendly Specification Format

Based on the user requirement for a tool that translates natural language specifications into a more precise, AI-consumable format for hierarchical coding tasks, and drawing upon research into formal methods, structured prompting, DSLs, ambiguity handling, and agent architectures, this document proposes an AI-friendly specification format.

The primary goals of this format are:

* **Precision:** Minimize ambiguity inherent in natural language.
* **AI Consumability:** Be easily parsable and interpretable by LLMs.
* **Decomposition:** Support breaking down complex tasks into smaller, manageable steps.
* **Hierarchy:** Accommodate hierarchical agent workflows (e.g., planner/executor).
* **Iterability:** Be suitable for generation and refinement by AI agents.
* **Flexibility:** Adaptable to various coding tasks, starting with parser/code generation.

### 3.1 Format Choice: YAML

YAML (YAML Ain't Markup Language) is chosen as the base format.

**Rationale:**

* **Structure:** Provides a strict hierarchical structure necessary for defining complex plans and specifications.
* **Readability:** Generally more human-readable than JSON, which can be beneficial during development and debugging.
* **Parsability:** Easily parsed by standard libraries in most programming languages, and LLMs demonstrate good capability in generating and parsing YAML.
* **Flexibility:** Supports various data types, multi-line strings (useful for detailed instructions or embedded code/prompts), lists, and dictionaries, allowing for a rich schema definition.

### 3.2 Proposed Schema

The proposed YAML schema consists of top-level metadata and a structured plan composed of individual steps.

```yaml
# --- Top-Level Metadata --- #

task_id: string # Unique identifier for the overall task (e.g., UUID)
natural_language_goal: string # The original, high-level user request
overall_context: | # Multi-line string
  # Provides shared background information, constraints, style guides,
  # relevant file paths, environment details, etc., applicable to all steps.
  # Example: "Target language is Python 3.11. Use PEP 8 standards."

# --- Hierarchical Plan --- #

plan:
  - # --- Step Definition --- #
    step_id: string # Unique identifier for this step within the task (e.g., "generate_parser_core")
    description: string # Human-readable description of the step's purpose
    depends_on: [string] # List of step_ids that must be completed before this step can start
    input-hash: string # provided by the input and written here to detect if any changes have happened to the input used to generate this file
    
    # --- Agent Specification for this Step --- #
    agent_spec:
      type: string # Categorizes the step type for potential agent routing (e.g., "planning", "code_generation", "code_analysis", "testing", "refinement", "documentation")
      input_artifacts: [string] # List of required input file paths or data identifiers (referencing outputs of previous steps or initial context)
      output_artifacts: [string] # List of expected output file paths or data identifiers generated by this step

      instructions: | # Multi-line string
        # Detailed, potentially structured instructions for the AI agent executing this step.
        # Can leverage structured prompting techniques (e.g., numbered steps, role definition).
        # Example:
        # "Role: Python Code Generator
        # Task: Implement the core parsing function based on the grammar defined in {input_artifacts[0]}.
        # 1. Read the grammar specification.
        # 2. Generate Python code using the 'argparse' library (if applicable).
        # 3. Include error handling for invalid input formats.
        # 4. Write the generated code to {output_artifacts[0]}."

      # Optional: More specific constraints or requirements
      constraints: [string] # List of specific rules or conditions the output must satisfy
        # Example: "- Function complexity must be low."
        # Example: "- Must not use external libraries beyond the standard library."

      # Optional: Criteria for validating step completion/success
      validation_criteria: [string] # List of conditions to check for successful completion
        # Example: "- Output file {output_artifacts[0]} exists."
        # Example: "- Code passes linting checks (e.g., flake8)."
        # Example: "- Unit tests defined in 'test_spec.yaml' pass."

      # Optional: Guidance for model selection via OpenRouter
      model_preference:
        # Allows suggesting specific models or capabilities for this step
        provider: string # e.g., "openai", "anthropic", "google", "mistral", "together"
        model: string # e.g., "gpt-4o", "claude-3-opus-20240229", "gemini-1.5-pro", "mistral-large-latest"
        # Could also include capability hints: "fast", "cheap", "strong_reasoning", "good_at_code"
        # Or specific parameters like temperature, max_tokens
        temperature: float # Optional: e.g., 0.7
        max_tokens: int # Optional: e.g., 4096

  - # --- Another Step Definition --- #
    step_id: "run_unit_tests"
    description: "Execute unit tests against the generated code"
    depends_on: ["generate_parser_core"]
    agent_spec:
      type: "testing"
      input_artifacts: ["output/parser_core.py", "data/test_cases.json", "specs/test_spec.yaml"]
      output_artifacts: ["results/test_summary.json"]
      instructions: | # Multi-line string
        # "1. Use the test specification in {input_artifacts[2]} to run tests.
        #  2. Execute the code in {input_artifacts[0]} against test cases in {input_artifacts[1]}.
        #  3. Record detailed results (pass/fail per test, errors) in {output_artifacts[0]} using JSON format."
      validation_criteria: ["- {output_artifacts[0]} contains valid JSON.", "- All mandatory tests in spec pass."]
      model_preference:
        model: "gpt-4o-mini" # Cheaper model potentially sufficient for running tests/interpreting results

# --- Optional: State for Iterative Refinement --- #
# This section could be added/updated by a meta-agent managing the process

# refinement_state:
#   current_iteration: int
#   last_step_failed: string # step_id of the last failure
#   feedback_summary: | # Multi-line string
#     # Summary of issues from validation/testing steps
#     # Example: "Step 'generate_parser_core' failed validation: Code did not compile due to SyntaxError on line 42."
#   suggested_next_action: string # e.g., "retry_step", "modify_instructions", "request_human_input"

```

### 3.3 Rationale for Schema Components

* **`task_id`, `natural_language_goal`, `overall_context`:** Provide essential grounding and tracking.
* **`plan` (List of Steps):** Enables decomposition.
* **`step_id`, `description`, `depends_on`:** Define the workflow structure and dependencies, allowing for parallel execution where possible.
* **`agent_spec`:** Encapsulates everything needed for a specific agent to execute a step.
  * **`type`:** Facilitates routing to different agent implementations or prompt templates.
  * **`input_artifacts`, `output_artifacts`:** Make data flow explicit.
  * **`instructions`:** The core prompt/task description for the LLM, allowing detailed natural language combined with structured elements.
  * **`constraints`, `validation_criteria`:** Introduce precision and objective measures of success, reducing ambiguity and enabling automated checks or feedback loops.
  * **`model_preference`:** Directly leverages OpenRouter's flexibility for cost/performance optimization in hierarchical setups.
* **`refinement_state` (Optional):** Provides a potential mechanism for managing the iterative refinement loop suggested by the user, allowing a meta-agent to track progress, failures, and feedback.

This proposed format provides a solid foundation, balancing structure for AI consumption with flexibility for expressing complex coding tasks. It serves as a practical starting point, potentially evolving towards a more optimized AI-specific format in future iterations.

## 4. Design: Iterative Tool Architecture

This section outlines the proposed architecture for the AI coding assistant tool. It builds upon the research findings and the designed AI-friendly specification format (YAML). The architecture emphasizes a hierarchical, iterative approach, leveraging multiple AI models via OpenRouter to translate natural language goals into executable code, with mechanisms for validation and refinement, including a pre-execution understanding check.

### 4.1 Core Components

The system comprises several key components:

1. **User Interface (Conceptual):** Where the user initially provides the high-level natural language goal.
2. **Orchestrator:** The central component managing the overall workflow, state, and interaction between agents.
3. **Planner Agent:** A high-capability LLM responsible for decomposing the user goal into the structured YAML specification format and evaluating executor understanding.
4. **Executor Agent(s):** One or more LLMs (potentially specialized or lower-cost) responsible for executing individual steps defined in the YAML plan.
5. **Validation Module:** Executes checks defined in the `validation_criteria` of each step (e.g., running linters, unit tests, or using another LLM for semantic checks).
6. **Specification Store:** Stores the current version of the YAML specification file.
7. **Artifact Store:** Stores input/output files (code, data, results) generated during the process.

### 4.2 Workflow Overview

1. **Initialization:** User provides a natural language goal.
2. **Initial Planning:** Orchestrator invokes Planner Agent to generate the initial `task_spec.yaml`.
3. **Iterative Execution & Refinement Loop:** Orchestrator manages the execution of the plan.

* **Step Selection:** Orchestrator identifies the next ready step(s).
* **Pre-Execution Understanding Check & Refinement (New Loop):** For each ready step:
  * **a. Executor Summarization:** Orchestrator invokes the designated Executor Agent (selected via OpenRouter based on `model_preference` or defaults) with a specific prompt asking it to summarize its understanding of the task defined in `agent_spec.instructions` and how it plans to approach it, considering inputs/outputs.
    * **b. Summary Evaluation:** Orchestrator provides the Executor's summary and the original `agent_spec.instructions` to the Planner Agent (or a dedicated evaluation mechanism).
    * **c. Evaluation Decision:** The Planner Agent evaluates if the summary accurately reflects the intended task. It outputs a judgment (e.g., "satisfactory", "needs_refinement") and potentially specific feedback if refinement is needed.
    * **d. Instruction Refinement (if needed):** If the judgment is "needs_refinement", the Orchestrator invokes the Planner Agent again to modify the `agent_spec.instructions` in `task_spec.yaml` based on the evaluation feedback. The Orchestrator then loops back to step 3.a (Executor Summarization) with the updated instructions. This inner loop repeats until the summary is deemed "satisfactory" or a maximum pre-execution refinement iteration limit is reached.
    * **e. Proceed to Execution:** If the summary is "satisfactory", the Orchestrator proceeds to the next phase.
* **Executor Execution:** Orchestrator invokes the *same* Executor Agent (which has demonstrated understanding) to perform the actual task as described in the *now-validated* `instructions`.
        ***Input:** Validated `agent_spec`, required `input_artifacts`.
        * **Action:** Executor Agent performs the task.
        * **Output:** Generates `output_artifacts`.
* **Post-Execution Validation:** Orchestrator triggers the Validation Module for the completed step.
        ***Input:** `validation_criteria`, `output_artifacts`.
        * **Action:** Performs checks.
        * **Output:** Validation result (success/failure), feedback/errors.
  * **Post-Execution Feedback & Refinement (if validation fails):**
        *Orchestrator gathers validation feedback.
        * Orchestrator invokes the Planner Agent to analyze the failure.
        ***Action:** Planner Agent modifies `task_spec.yaml` (instructions, constraints, plan structure, model preference) or flags for human intervention.
        * **Output:** Updated `task_spec.yaml`.
        * Orchestrator restarts the outer loop, potentially re-executing the failed/modified step (including the pre-execution check).
  * **Loop Continuation:** The outer loop continues until all steps are successfully completed and validated, or a maximum iteration count is reached, or human intervention is required.

1. **Completion:** Orchestrator signals completion.

### 4.3 Agent Roles & Model Selection

* **Planner Agent:** Role expanded to include evaluating executor summaries and refining instructions pre-execution. Still requires high capability (e.g., GPT-4, Claude 3 Opus).
* **Executor Agent(s):** Role now includes generating a pre-execution summary. Model selection via OpenRouter remains flexible based on step type/preference.
* **Validation Agent (Optional):** Unchanged.

### 4.4 Iterative Refinement Loops

The architecture now includes two distinct iterative loops:

1. **Pre-Execution Loop (New):** Focuses on ensuring the Executor Agent understands the instructions *before* attempting execution. This loop involves the Executor summarizing and the Planner evaluating/refining instructions.
2. **Post-Execution Loop:** Focuses on validating the *outcome* of the execution and refining the plan or instructions if the outcome is unsatisfactory.

This dual-loop approach aims to catch misunderstandings early (pre-execution) and handle execution failures robustly (post-execution).

### 4.5 Error Handling

Error handling remains crucial. The pre-execution loop adds potential failure points (e.g., failure to generate a summary, max refinement iterations reached) that the Orchestrator must manage, potentially escalating to the post-execution refinement logic or human intervention.

This architecture provides a robust framework for the AI coding assistant tool, incorporating user feedback for enhanced instruction clarity and iterative refinement.
