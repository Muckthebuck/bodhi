import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ChatView } from "../components/ChatView";
import type { ChatMessage } from "../types";

const noop = () => {};

describe("ChatView", () => {
  const baseMsgs: ChatMessage[] = [
    { id: "1", role: "user", text: "Hello", timestamp: 1 },
    { id: "2", role: "companion", text: "Hi there!", timestamp: 2 },
    { id: "3", role: "system", text: "Error: timeout", timestamp: 3 },
  ];

  it("renders messages", () => {
    render(<ChatView messages={baseMsgs} onSend={noop} isConnected isThinking={false} />);
    expect(screen.getByText("Hello")).toBeInTheDocument();
    expect(screen.getByText("Hi there!")).toBeInTheDocument();
    expect(screen.getByText("Error: timeout")).toBeInTheDocument();
  });

  it("renders markdown in companion messages", () => {
    const msgs: ChatMessage[] = [
      { id: "md1", role: "companion", text: "**bold** and *italic*", timestamp: 1 },
    ];
    render(<ChatView messages={msgs} onSend={noop} isConnected isThinking={false} />);
    const bold = document.querySelector("strong");
    expect(bold).toBeInTheDocument();
    expect(bold?.textContent).toBe("bold");
  });

  it("shows empty state when no messages", () => {
    render(<ChatView messages={[]} onSend={noop} isConnected isThinking={false} />);
    expect(screen.getByText("No messages yet")).toBeInTheDocument();
  });

  it("shows thinking indicator", () => {
    render(<ChatView messages={[]} onSend={noop} isConnected isThinking />);
    expect(screen.getByText("Thinking…")).toBeInTheDocument();
  });

  it("disables input when disconnected", () => {
    render(<ChatView messages={[]} onSend={noop} isConnected={false} isThinking={false} />);
    const input = screen.getByPlaceholderText("Disconnected");
    expect(input).toBeDisabled();
  });

  it("calls onSend when submitting", () => {
    const onSend = vi.fn();
    render(<ChatView messages={[]} onSend={onSend} isConnected isThinking={false} />);
    const input = screen.getByPlaceholderText("Type a message…");
    fireEvent.change(input, { target: { value: "test msg" } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(onSend).toHaveBeenCalledOnce();
    expect(onSend.mock.calls[0][0]).toMatchObject({
      type: "user.message",
      text: "test msg",
    });
  });

  it("does not send empty messages", () => {
    const onSend = vi.fn();
    render(<ChatView messages={[]} onSend={onSend} isConnected isThinking={false} />);
    const input = screen.getByPlaceholderText("Type a message…");
    fireEvent.change(input, { target: { value: "   " } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(onSend).not.toHaveBeenCalled();
  });
});
