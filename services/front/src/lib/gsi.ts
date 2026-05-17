// Renders the exact VDF text block expected by Valve's dota2-gsi loader.
// Keep the formatting byte-for-byte stable: the on-screen block is meant to be
// copy-pasted directly into `cfg/gamestate_integration_<name>.cfg`.
export function buildGsiConfig(token: string, uri = "/gsi-input"): string {
  return `"dota2-gsi Configuration"
{
    "uri"          "${uri}"
    "timeout"      "5.0"
    "buffer"       "1.0"
    "throttle"     "1.0"
    "heartbeat"    "20.0"
    "data"
    {
        "auth"          "1"
        "provider"      "1"
        "map"           "1"
        "player"        "1"
        "hero"          "1"
        "abilities"     "1"
        "items"         "1"
        "events"        "1"
        "buildings"     "1"
        "league"        "1"
        "draft"         "1"
        "wearables"     "1"
        "minimap"       "1"
        "roshan"        "1"
        "couriers"      "1"
        "neutralitems"  "1"
        "players"       "1"
        "allplayers"    "1"
        "team"          "1"
        "teams"         "1"
        "radiant"       "1"
        "dire"          "1"
    }
    "auth"
    {
        "token"     "${token}"
    }
}`;
}
