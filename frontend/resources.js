/* Add reviewed resources only. Entries without verification metadata are not shown. */
const localDevelopment = ["localhost", "127.0.0.1"].includes(window.location.hostname);
window.SAFEHER_CONFIG = {
  // The deploy build writes the public API origin to runtime-config.js.
  // Only local development falls back to a loopback address.
  apiBaseUrl: window.SAFEHER_PUBLIC_CONFIG?.apiBaseUrl || (localDevelopment ? "http://127.0.0.1:8000" : ""),
  mapTileUrlTemplate: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
  mapTileAttribution: "&copy; <a href=\"https://www.openstreetmap.org/copyright\">OpenStreetMap contributors</a>",
  emergencyResources: [],
  nearbyResources: []
};
