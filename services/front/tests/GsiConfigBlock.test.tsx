import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { GsiConfigBlock } from "@/components/GsiConfigBlock";

describe("GsiConfigBlock", () => {
  it("renders the configuration with the generated token embedded", () => {
    render(<GsiConfigBlock token="deadbeef" />);
    expect(screen.getByText(/"dota2-gsi Configuration"/)).toBeInTheDocument();
    const pre = screen.getByText(/"dota2-gsi Configuration"/).closest("pre");
    expect(pre?.textContent).toContain('"token"     "deadbeef"');
    expect(pre?.textContent).toContain('"uri"          "http://localhost:3000/"');
  });

  it("shows a Copy button", () => {
    render(<GsiConfigBlock token="t" />);
    expect(screen.getByRole("button", { name: /copy/i })).toBeInTheDocument();
  });
});
