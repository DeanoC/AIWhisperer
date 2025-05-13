# Plan to Update Terminal Monitor Documentation

This document outlines the plan to update the project documentation to reflect the new terminal monitor features.

**Objective:** Ensure documentation in [`docs/logging_monitoring.md`](docs/logging_monitoring.md) and [`README.md`](README.md) is clear, accurate, and consistent with the implemented terminal monitor enhancements as detailed in [`docs/monitor_terminal_analysis.md`](docs/monitor_terminal_analysis.md).

## 1. Understand New Terminal Monitor Features

Based on [`docs/monitor_terminal_analysis.md`](docs/monitor_terminal_analysis.md), the key features are:

*   **Screen Splitting:**
    *   Three main horizontal segments: Left, Center, Right.
    *   Central segment subdivided vertically:
        *   Top (larger): Primary monitor output.
        *   Bottom (smaller): Command box (future use).
    *   Left/Right segments: Currently empty, reserved for future content.
*   **ASCII Outlines:**
    *   All primary segments and the central subdivision are visually separated by ASCII art boxes/lines.
*   **Output Suppression:**
    *   Non-monitor related output (general CLI logs, etc.) is suppressed from the main terminal window when the monitor is active.
    *   Only designated monitor events appear in the primary monitor output area.
*   **Coloring & Formatting:**
    *   Different types/levels of terminal events are distinguished using colors.
    *   JSON strings displayed in the monitor are pretty-printed.
    *   Pretty-printed JSON utilizes syntax highlighting with colors.
*   **Logging Integration:**
    *   The monitor displays designated monitor events, implying it filters or processes messages from the main logging system.

## 2. Update [`docs/logging_monitoring.md`](docs/logging_monitoring.md)

*   **Modify the "Terminal Monitoring View" section:**
    *   **Update "Information Displayed":**
        *   Replace the current panel description with the new three-segment layout:
            *   Clearly describe the left, center, and right horizontal segments.
            *   Detail the central segment's vertical subdivision: main monitor output area and command box.
            *   Mention the use of ASCII art for outlining.
        *   Specify that the central monitor output area is the primary focus.
    *   **Add/Integrate "Key Monitor Features":**
        *   **Output Suppression:** Explain suppression of non-monitor output.
        *   **Colored Output:** Describe color-coding for event types/levels.
        *   **JSON Pretty-Printing:** State automatic pretty-printing and syntax highlighting for JSON.
    *   **Add new subsection: "Integration with the Logging System":**
        *   Explain the monitor as a specialized real-time viewer for the logging system.
        *   Clarify it displays relevant `LogMessage` entries.
        *   Reiterate that comprehensive logs are still stored in files.
    *   **Review "Interactive Features":** Confirm relevance and interaction with the new layout.

## 3. Update [`README.md`](README.md)

*   **In the "Features" section:**
    *   Add a new bullet point:
        *   "**Improved Terminal Monitor:** A redesigned real-time terminal monitor display featuring three segmented, ASCII-outlined sections, colored output for event types, pretty-printed and syntax-highlighted JSON for monitor events, and suppression of non-monitor output for a cleaner view of plan execution."
*   **Optionally, enhance the `run` command description:**
    *   After mentioning `--monitor` or `-m`, add a brief note like: "(now with an enhanced multi-section display, colored output, and more!)."

## 4. Review and Ensure Consistency

*   Thoroughly review changes in both documentation files.
*   Ensure descriptions accurately reflect features from [`docs/monitor_terminal_analysis.md`](docs/monitor_terminal_analysis.md).
*   Check for clarity, conciseness, and consistent terminology.

## Mermaid Diagram of the Plan

```mermaid
graph TD
    A[Start: Update Documentation Task] --> B{Read docs/monitor_terminal_analysis.md};
    B --> C{Read current docs/logging_monitoring.md};
    C --> D{Read current README.md};
    D --> E[Develop Detailed Update Plan];

    E --> F[Update docs/logging_monitoring.md];
    F --> F1[Modify 'Terminal Monitoring View' Section];
    F1 --> F1a[Update 'Information Displayed' with 3-segment layout & ASCII outlines];
    F1 --> F1b[Add 'Key Monitor Features': Output Suppression, Colored Output, JSON Pretty-Printing];
    F1 --> F1c[Add 'Integration with Logging System' subsection];
    F1 --> F1d[Review 'Interactive Features'];

    E --> G[Update README.md];
    G --> G1[Add new bullet point to 'Features' section describing improved monitor];
    G --> G2[Optional: Enhance 'run' command description for --monitor flag];

    F --> H{Review Updated docs/logging_monitoring.md};
    G --> I{Review Updated README.md};

    H --> J[Final Check: Ensure Accuracy & Consistency with Analysis Doc];
    I --> J;
    J --> K[End: Documentation Updated];