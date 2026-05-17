import { describe, expect, it } from "vitest";
import { generateToken } from "@/lib/token";

describe("generateToken", () => {
  it("returns a hex string of the requested length", () => {
    const tok = generateToken(32);
    expect(tok).toHaveLength(32);
    expect(tok).toMatch(/^[0-9a-f]+$/);
  });

  it("produces unique values across calls", () => {
    const tokens = new Set(Array.from({ length: 16 }, () => generateToken()));
    expect(tokens.size).toBe(16);
  });
});
