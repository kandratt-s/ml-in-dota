import { useEffect, useRef } from "react";

interface HeatmapCanvasProps {
  matrix: number[][] | null;
  maxValue?: number;
  // CSS class applied to the canvas wrapper; the canvas itself fills it.
  className?: string;
}

// Mirrors the old Streamlit plotly stops:
//   0.0 -> rgba(255,0,0,0.0)
//   0.2 -> rgba(255,0,0,0.2)
//   0.5 -> rgba(255,0,0,0.5)
//   1.0 -> rgba(255,0,0,0.9)
function alphaForRatio(ratio: number): number {
  const r = Math.max(0, Math.min(1, ratio));
  const stops: Array<[number, number]> = [
    [0.0, 0.0],
    [0.2, 0.2],
    [0.5, 0.5],
    [1.0, 0.9],
  ];
  for (let i = 1; i < stops.length; i++) {
    const [x1, a1] = stops[i];
    if (r <= x1) {
      const [x0, a0] = stops[i - 1];
      const t = (r - x0) / (x1 - x0);
      return a0 + (a1 - a0) * t;
    }
  }
  return stops[stops.length - 1][1];
}

// HeatmapCanvas draws an N×N matrix into a same-size offscreen canvas and
// the browser scales it up via CSS. `image-rendering: pixelated` keeps the
// scale-up crisp, so each matrix cell renders as a solid square with no
// smoothing between neighbours.
export function HeatmapCanvas({ matrix, maxValue, className }: HeatmapCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    if (!matrix || matrix.length === 0) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      return;
    }

    const cells = matrix.length;
    if (canvas.width !== cells || canvas.height !== cells) {
      canvas.width = cells;
      canvas.height = cells;
    }

    const max = maxValue && maxValue > 0 ? maxValue : flatMax(matrix) || 1;

    const img = ctx.createImageData(cells, cells);
    for (let r = 0; r < cells; r++) {
      const row = matrix[r] ?? [];
      // Flip vertically: plotly's matrix[0] sits at the bottom of the y-axis,
      // canvas y=0 is the top. This keeps the visual aligned with the old UI.
      const dstRow = cells - 1 - r;
      for (let c = 0; c < cells; c++) {
        const a = alphaForRatio((row[c] ?? 0) / max);
        const idx = (dstRow * cells + c) * 4;
        img.data[idx] = 255;       // R
        img.data[idx + 1] = 0;     // G
        img.data[idx + 2] = 0;     // B
        img.data[idx + 3] = Math.round(a * 255);
      }
    }
    ctx.putImageData(img, 0, 0);
  }, [matrix, maxValue]);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className={`absolute inset-0 h-full w-full pointer-events-none ${className ?? ""}`}
      style={{ imageRendering: "pixelated" }}
    />
  );
}

function flatMax(m: number[][]): number {
  let max = 0;
  for (const row of m) for (const v of row) if (v > max) max = v;
  return max;
}
