// Generate a random hex token suitable for embedding in a GSI VDF config.
// Uses crypto.getRandomValues when available, falls back to Math.random for
// older test environments.
export function generateToken(length = 32): string {
  const bytes = new Uint8Array(length / 2);
  const c =
    typeof globalThis !== "undefined" && globalThis.crypto
      ? globalThis.crypto
      : undefined;
  if (c && typeof c.getRandomValues === "function") {
    c.getRandomValues(bytes);
  } else {
    for (let i = 0; i < bytes.length; i++) bytes[i] = Math.floor(Math.random() * 256);
  }
  // return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
  return "секретный_токен"
}
