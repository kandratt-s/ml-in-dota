import { describe, expect, it } from "vitest";
import { buildGsiConfig } from "@/lib/gsi";

describe("buildGsiConfig", () => {
  it("injects the token into the auth block", () => {
    const out = buildGsiConfig("abc123");
    expect(out).toContain('"token"     "abc123"');
  });

  it("uses the default URI when none is provided", () => {
    const out = buildGsiConfig("t");
    expect(out).toContain('"uri"          "http://localhost:3000/"');
  });

  it("allows overriding the URI", () => {
    const out = buildGsiConfig("t", "http://example.com/");
    expect(out).toContain('"uri"          "http://example.com/"');
  });

  it("starts with the expected header line", () => {
    expect(buildGsiConfig("t").split("\n")[0]).toBe('"dota2-gsi Configuration"');
  });

  it("contains the full data block keys", () => {
    const out = buildGsiConfig("t");
    for (const key of [
      "provider",
      "map",
      "player",
      "hero",
      "abilities",
      "items",
      "events",
      "buildings",
      "minimap",
      "roshan",
      "allplayers",
    ]) {
      expect(out).toContain(`"${key}"`);
    }
  });
});
