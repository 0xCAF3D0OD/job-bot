// Une panne de réseau, pas une erreur du serveur (planche « Illustrations ») : le navigateur se dit hors
// ligne, ou la requête n'a pas pu partir (fetch lève une TypeError). Une erreur du serveur garde son
// propre message.
export function isNetworkError(error: unknown): boolean {
  if (globalThis.navigator && globalThis.navigator.onLine === false) return true;
  return error instanceof TypeError;
}
