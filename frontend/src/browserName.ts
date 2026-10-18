// Le nom du navigateur, pour reconnaître un jeton de l'extension dans Réglages (docs/25, docs/71).
export function browserName(agent: string = globalThis.navigator?.userAgent ?? ""): string {
  if (agent.includes("Firefox/")) return "Firefox";
  if (agent.includes("Edg/")) return "Edge";
  if (agent.includes("Brave")) return "Brave";
  if (agent.includes("Chrome/")) return "Chrome";
  return "Mon navigateur";
}
