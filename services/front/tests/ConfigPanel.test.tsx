import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ConfigPanel } from "@/components/ConfigPanel";
import { DEFAULT_CONFIG, type SessionConfig } from "@/types/config";

describe("ConfigPanel", () => {
  it("renders defaults with boosting and time 10 selected", () => {
    render(<ConfigPanel config={DEFAULT_CONFIG} onChange={() => {}} disabled={false} />);
    const boosting = screen.getByRole("radio", { name: "boosting" });
    const time10 = screen.getByRole("radio", { name: "10" });
    expect(boosting).toHaveAttribute("aria-checked", "true");
    expect(time10).toHaveAttribute("aria-checked", "true");
  });

  it("emits a new config when a different model is chosen", async () => {
    const onChange = vi.fn();
    render(<ConfigPanel config={DEFAULT_CONFIG} onChange={onChange} disabled={false} />);
    await userEvent.click(screen.getByRole("radio", { name: "logreg" }));
    expect(onChange).toHaveBeenCalledWith({ ...DEFAULT_CONFIG, model: "logreg" });
  });

  it("emits a new config when interval changes", async () => {
    const onChange = vi.fn();
    render(<ConfigPanel config={DEFAULT_CONFIG} onChange={onChange} disabled={false} />);
    await userEvent.click(screen.getByRole("radio", { name: "3" }));
    expect(onChange).toHaveBeenCalledWith({ ...DEFAULT_CONFIG, interval: 3 });
  });

  it("disables all chips while running", () => {
    render(<ConfigPanel config={DEFAULT_CONFIG} onChange={() => {}} disabled={true} />);
    for (const r of screen.getAllByRole("radio")) {
      expect(r).toBeDisabled();
    }
  });

  it("toggles the full_map switch", async () => {
    const onChange = vi.fn();
    const cfg: SessionConfig = { ...DEFAULT_CONFIG, full_map: true };
    render(<ConfigPanel config={cfg} onChange={onChange} disabled={false} />);
    await userEvent.click(screen.getByRole("switch", { name: /full map/i }));
    expect(onChange).toHaveBeenCalledWith({ ...cfg, full_map: false });
  });
});
