# Prompt: Refine Rough Requirements Document

## Goal

Transform a rough, potentially unstructured, requirements document (provided in Markdown format) into a clear, concise, and high-level natural language requirement. This refined requirement should be suitable for a subsequent AI to understand and use as a basis for generating a detailed execution plan.

## Input

A Markdown document containing the initial, rough requirements. This document might include:

- User stories
- Feature requests
- Technical notes
- Unclear or ambiguous statements
- Mixed levels of detail

## Output

A single, coherent, high-level natural language requirement that:

1. **Summarizes the core need:** Clearly articulates the primary objective or problem to be solved.
2. **Is unambiguous:** Eliminates jargon where possible, clarifies vague terms, and resolves contradictions.
3. **Focuses on "what," not "how":** Describes the desired outcome and essential functionalities, deferring implementation details.
4. **Is concise:** Removes redundant information and overly specific details that are not critical at the high-level planning stage.
5. **Is structured for AI understanding:** Presents the information in a way that is easy for another AI to parse and act upon (e.g., clear statements, logical flow).
6. **Maintains key constraints:** Preserves any critical constraints or non-negotiable elements from the original document.
7. **Content Fidelity:** Ensures the refined requirement is a direct transformation of the *input document's content and scope*, without introducing unrelated concepts, domains, or defaulting to generic examples if the input is specific.

## Instructions for the AI

1. **Understand the Input:** Carefully read and analyze the provided rough requirements document. Identify the main goals, key features, and any critical constraints. *Focus exclusively on the content and scope presented within this document.*
2. **Identify Core Objectives:** Distill the essence of the requirements. What is the fundamental problem being solved or the primary value being delivered?
3. **Clarify and Consolidate:**
    - Rephrase ambiguous statements into clear, direct language.
    - Group related ideas and features.
    - Resolve any apparent contradictions or inconsistencies, making reasonable assumptions if necessary (and noting them if significant).
4. **Abstract to High Level:** Focus on the strategic "what" and "why." Avoid getting bogged down in low-level implementation details ("how"). If the input contains detailed technical specifications, summarize their intent at a higher level.
5. **Synthesize the Refined Requirement:** Construct a new, single natural language statement or a short series of closely related statements that encapsulate the refined understanding. *The synthesized requirement must directly reflect the subject matter, domain, and specific goals of the input document. Avoid introducing external topics or generating requirements for unrelated systems.*
    - Start with a clear overarching goal.
    - Enumerate key capabilities or outcomes if necessary.
    - Ensure the language is natural, flowing, and easy to understand.
6. **Review and Iterate (Internal):** Before finalizing, mentally review the refined requirement against the original document. Does it accurately capture the intent? Is it clear and actionable for a planning AI?

## Example Transformation (Conceptual)

**Rough Input (Excerpt):**
"User wants a button. When clicked, it should show a popup. The popup needs to have user data from the backend. API endpoint is /api/userdata. Make it blue. Also, need to track clicks for analytics."

**Refined Output (Conceptual):**
"Enhance the system to provide a capability for users to access and view their personalized data. This capability must involve retrieving user-specific information from a designated data source and presenting it in a clear format. Interactions related to this capability should be logged for analytical purposes. *Note: This is an example of structure and refinement; the actual content of your output must be derived solely from the provided rough input document.*"

---
**BEGIN ROUGH REQUIREMENTS DOCUMENT:**

{{{requirements}}}

---
**END ROUGH REQUIREMENTS DOCUMENT.**

**BEGIN REFINED HIGH-LEVEL REQUIREMENT:**
