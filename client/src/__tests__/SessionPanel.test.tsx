import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { SessionPanel } from "../components/SessionPanel";

beforeEach(() => {
  localStorage.clear();
});

describe("SessionPanel", () => {
  it("renders current session", () => {
    render(<SessionPanel currentSession="default" onSwitch={() => {}} />);
    expect(screen.getByText(/default/)).toBeInTheDocument();
  });

  it("can create a new session", () => {
    const onSwitch = vi.fn();
    render(<SessionPanel currentSession="default" onSwitch={onSwitch} />);
    // Expand the panel
    fireEvent.click(screen.getByText(/default/));
    const input = screen.getByPlaceholderText("new-session");
    fireEvent.change(input, { target: { value: "test-session" } });
    fireEvent.click(screen.getByText("+"));
    expect(onSwitch).toHaveBeenCalledWith("test-session");
  });

  it("can delete a session", () => {
    // Pre-populate sessions
    localStorage.setItem("bodhi-sessions", JSON.stringify(["default", "other"]));
    const onDelete = vi.fn();
    const onSwitch = vi.fn();
    // Mock confirm to always return true
    vi.spyOn(window, "confirm").mockReturnValue(true);

    render(<SessionPanel currentSession="default" onSwitch={onSwitch} onDelete={onDelete} />);
    fireEvent.click(screen.getByText(/default/));

    // Find delete button for "other" session
    const deleteButtons = screen.getAllByTitle(/Delete/);
    expect(deleteButtons.length).toBeGreaterThanOrEqual(1);
    fireEvent.click(deleteButtons[deleteButtons.length - 1]);
    expect(onDelete).toHaveBeenCalledWith("other");
  });

  it("prevents deleting the last session", () => {
    localStorage.setItem("bodhi-sessions", JSON.stringify(["default"]));
    render(<SessionPanel currentSession="default" onSwitch={() => {}} />);
    fireEvent.click(screen.getByText(/default/));
    // Should not show delete button when only 1 session
    expect(screen.queryAllByTitle(/Delete/)).toHaveLength(0);
  });
});
