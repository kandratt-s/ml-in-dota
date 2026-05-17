import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { StartStopButton } from "@/components/StartStopButton";

describe("StartStopButton", () => {
  it("shows Start when not running", () => {
    render(<StartStopButton running={false} busy={false} onToggle={() => {}} />);
    expect(screen.getByRole("button", { name: "Start" })).toBeInTheDocument();
  });

  it("shows Stop when running", () => {
    render(<StartStopButton running={true} busy={false} onToggle={() => {}} />);
    expect(screen.getByRole("button", { name: "Stop" })).toBeInTheDocument();
  });

  it("invokes onToggle on click", async () => {
    const onToggle = vi.fn();
    render(<StartStopButton running={false} busy={false} onToggle={onToggle} />);
    await userEvent.click(screen.getByRole("button"));
    expect(onToggle).toHaveBeenCalledOnce();
  });

  it("is disabled while busy", () => {
    render(<StartStopButton running={false} busy={true} onToggle={() => {}} />);
    expect(screen.getByRole("button")).toBeDisabled();
  });
});
