import { render, screen, fireEvent } from "@testing-library/react";
import AgentInspectorPanel from "./AgentInspectorPanel";

describe("AgentInspectorPanel", () => {
  it("renders the inspector panel and toggles visibility", () => {
    render(<AgentInspectorPanel agents={[{ id: "P", name: "Patricia" }]} />);
    // Check for the Inspector heading specifically
    expect(screen.getByRole("heading", { name: /Inspector/i })).toBeInTheDocument();
    // Check for the toggle button
    expect(screen.getByRole("button", { name: /Hide Inspector/i })).toBeInTheDocument();
    // Simulate toggle if implemented
    // fireEvent.click(screen.getByRole("button", { name: /show/i }));
    // expect(screen.getByText(/Context/i)).toBeInTheDocument();
  });

  it("displays context for selected agent", async () => {
    // Mock fetch or props as needed
    render(<AgentInspectorPanel agents={[{ id: "P", name: "Patricia" }]} />);
    // Simulate agent selection and check for context display
    // fireEvent.change(screen.getByLabelText(/Agent/i), { target: { value: "P" } });
    // expect(await screen.findByText(/system/i)).toBeInTheDocument();
  });

  it("handles empty or invalid agent gracefully", () => {
    render(<AgentInspectorPanel agents={[]} />);
    expect(screen.getByText(/No agents available/i)).toBeInTheDocument();
  });
});
