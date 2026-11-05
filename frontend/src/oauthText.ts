// Se connecter avec Apple, Google ou Microsoft (docs/65, complément du 2026-11-05) : les fournisseurs dans l'ordre de
// la maquette Connexion, et les phrases des retours du serveur (`?erreur=…&fournisseur=…`, `?info=demande`).
export const PROVIDERS = ["apple", "google", "microsoft"] as const;
export type Provider = (typeof PROVIDERS)[number];

export const PROVIDER_LABEL: Record<Provider, string> = { apple: "Apple", google: "Google", microsoft: "Microsoft" };

export function isProvider(value: unknown): value is Provider {
  return typeof value === "string" && (PROVIDERS as readonly string[]).includes(value);
}

// Les fournisseurs rendus par GET /api/auth/providers, dans l'ordre de la maquette ; tout autre nom est ignoré.
export function knownProviders(list: unknown): Provider[] {
  const names = Array.isArray(list) ? list : [];
  return PROVIDERS.filter((name) => names.includes(name));
}

// L'adresse de départ : la page où revenir (?suite=) ou « lier » depuis Compte, Connexions.
export function startHref(provider: Provider, options: { suite?: string; link?: boolean } = {}): string {
  const query = new URLSearchParams();
  if (options.link) query.set("lier", "1");
  if (options.suite) query.set("suite", options.suite);
  const tail = query.toString();
  return `/api/auth/oauth/${provider}/start${tail ? `?${tail}` : ""}`;
}

export function oauthMessage(code: unknown, provider: unknown): string {
  const name = isProvider(provider) ? PROVIDER_LABEL[provider] : "ce fournisseur";
  switch (code) {
    case "aucun-compte":
      return `Aucun compte jobA1 n'est lié à ce compte ${name}.`;
    case "en-attente":
      return "Ton compte attend encore la validation de l'exploitant.";
    case "suspendu":
      return "Ce compte est suspendu : vois avec l'exploitant de la plateforme.";
    case "annule":
      return `Connexion avec ${name} annulée.`;
    case "expire":
      return "La connexion a pris trop de temps. Réessaie.";
    case "indisponible":
      return `${name} ne répond pas pour le moment. Réessaie, ou utilise ton identifiant.`;
    case "trop-de-demandes":
      return "Trop de demandes depuis cette adresse. Réessaie dans une heure.";
    case "deja-lie":
      return `Ce compte ${name} est déjà lié à un autre compte jobA1.`;
    case "demande":
      return `Ta demande de compte est envoyée. Tu pourras te connecter avec ${name} quand l'exploitant l'aura acceptée.`;
    default:
      return `La connexion avec ${name} n'a pas pu être vérifiée. Réessaie.`;
  }
}
