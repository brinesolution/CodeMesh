import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ContextMeshButton } from "./ContextMeshButton";

describe("ContextMeshButton", () => {
  it("expands on hover with honest counts and collapses when the pointer leaves", () => {
    render(<ContextMeshButton onClick={vi.fn()} memoryCount={3} recentCount={6} />);
    const button = screen.getByRole("button", { name: "Open Context Mesh" });

    expect(button).toHaveTextContent("Mesh");
    expect(button).not.toHaveTextContent("Context Mesh");
    fireEvent.mouseEnter(button);
    expect(button).toHaveTextContent("Context Mesh");
    expect(button).toHaveTextContent("3 memories · 6 recent");
    fireEvent.mouseLeave(button);
    expect(button).toHaveTextContent("Mesh");
    expect(button).not.toHaveTextContent("3 memories · 6 recent");
  });

  it("opens the persistent visualizer when clicked", () => {
    const onClick = vi.fn();
    render(<ContextMeshButton onClick={onClick} />);
    fireEvent.click(screen.getByRole("button", { name: "Open Context Mesh" }));
    expect(onClick).toHaveBeenCalledOnce();
  });
});
