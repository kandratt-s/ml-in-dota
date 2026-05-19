import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import { HeatmapCanvas, heatmapDisplayMax } from "@/components/HeatmapCanvas";

// Note: jsdom does not implement a real canvas 2D context, so pixel-level
// behaviour is covered by the in-browser smoke test. These tests just make
// sure the component mounts and accepts the expected props without throwing.
describe("HeatmapCanvas", () => {
  it("uses a minimum display scale of 1 for low maxima", () => {
    expect(heatmapDisplayMax(0.2)).toBe(1);
    expect(heatmapDisplayMax(0)).toBe(1);
    expect(heatmapDisplayMax(1.4)).toBe(1.4);
  });

  it("renders a canvas element when given a matrix", () => {
    const matrix = [
      [0, 0.5],
      [1, 0.25],
    ];
    const { container } = render(<HeatmapCanvas matrix={matrix} maxValue={1} />);
    expect(container.querySelector("canvas")).not.toBeNull();
  });

  it("renders without errors when matrix is null", () => {
    const { container } = render(<HeatmapCanvas matrix={null} />);
    expect(container.querySelector("canvas")).not.toBeNull();
  });

  it("renders without errors when matrix is empty", () => {
    const { container } = render(<HeatmapCanvas matrix={[]} />);
    expect(container.querySelector("canvas")).not.toBeNull();
  });
});
