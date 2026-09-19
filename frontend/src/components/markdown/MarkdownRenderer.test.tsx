import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MarkdownRenderer } from "./MarkdownRenderer";

describe("MarkdownRenderer math", () => {
  it("renders inline and display LaTeX while preserving fenced code", () => {
    const { container } = render(
      <MarkdownRenderer
        content={'Inline $F = ma$ and a block:\n\n$$\n\\frac{20}{5} = 4\\ \\text{m/s}^2\n$$\n\n```latex\n$F = ma$\n```'}
      />,
    );

    expect(container.querySelectorAll(".katex")).toHaveLength(2);
    expect(container.querySelector(".katex-display")).toBeInTheDocument();
    expect(container.querySelector(".code-block code")).toHaveTextContent("$F = ma$");
    expect(container.querySelector(".code-block .katex")).not.toBeInTheDocument();
  });

  it("supports bracketed LaTeX delimiters emitted by some local models", () => {
    const { container } = render(<MarkdownRenderer content={String.raw`Inline \(x^2\) and block:

\[
e^{i\pi} + 1 = 0
\]`} />);

    expect(container.querySelectorAll(".katex")).toHaveLength(2);
    expect(container.querySelector(".katex-display")).toBeInTheDocument();
  });
});
