import { computed, ref } from "vue";

import { api } from "../api/client";
import { useAuth } from "./useAuth";

// L'image de profil (maquette du 8 novembre, docs/143 §6) : les initiales par défaut, un des 8 avatars ou une photo.
// Le numéro de l'avatar est gardé par le serveur, comme les coordonnées (/api/profile-image). La photo importée
// (JPG ou PNG, 5 Mo au plus) est recadrée en cercle et réduite à 256 px dans le navigateur, puis gardée dans ce
// navigateur seulement : elle n'est jamais envoyée au serveur, à l'IA ni aux employeurs.

export const AVATARS = ["Souriant", "Clin d'œil", "Casque", "Lunettes", "Bonnet", "Écharpe", "Café", "Étoile"] as const;
export const PHOTO_MAX_BYTES = 5 * 1024 * 1024;
// La photo est rangée au nom du compte (incident du 2026-11-09) : sur un navigateur partagé, un autre compte ne
// voit jamais celle du précédent. L'ancienne clé, sans compte, est effacée sans être lue.
const PHOTO_PREFIX = "joba1.profile-photo:";
const OLD_PHOTO_KEY = "joba1.profile-photo";

export type ImageChoice = { kind: "initials" } | { kind: "avatar"; avatar: number } | { kind: "photo"; src: string };

const avatar = ref<number | null>(null);
const photo = ref<string | null>(null);
const fullName = ref<string | null>(null);
// L'e-mail de la fiche d'identité, montré à l'utilisateur seul (en-tête du panneau du compte) ; jamais envoyé ailleurs.
const email = ref<string | null>(null);
// La ville de la fiche d'identité : sous le nom, en tête du Profil (maquette ProfilOrdinateur).
const city = ref<string | null>(null);
let loading: Promise<void> | null = null;
// Le compte dont l'image, le nom et la ville sont en mémoire : un autre compte les relit (incident du 2026-11-09).
let loadedFor: string | null = null;

function photoKey(account: string): string {
  return PHOTO_PREFIX + account;
}
function readPhoto(account: string | null): string | null {
  try {
    globalThis.localStorage?.removeItem(OLD_PHOTO_KEY);
    return account ? (globalThis.localStorage?.getItem(photoKey(account)) ?? null) : null;
  } catch {
    return null;
  }
}
function writePhoto(account: string | null, value: string | null): void {
  if (!account) return;
  try {
    if (value) globalThis.localStorage?.setItem(photoKey(account), value);
    else globalThis.localStorage?.removeItem(photoKey(account));
  } catch {
    // Stockage refusé (navigation privée) : la photo reste pour cette visite.
  }
}

/** Oublie l'image, le nom, l'e-mail et la ville gardés en mémoire (changement de compte, tests). */
export function forgetProfileImage(): void {
  avatar.value = null;
  photo.value = null;
  fullName.value = null;
  email.value = null;
  city.value = null;
  loading = null;
  loadedFor = null;
}

/** « Kevin Di Nocera » en « KD » (les deux premiers mots, maquette ProfilOrdinateur) ; un seul mot : sa lettre. */
export function initialsOf(name: string | null | undefined): string {
  const words = (name ?? "").trim().split(/\s+/).filter(Boolean);
  return words.slice(0, 2).map((word) => word.charAt(0).toUpperCase()).join("");
}

export function avatarSrc(n: number, size: 128 | 256 = 128): string {
  return `/avatars/avatar-${n}-${size}.webp`;
}

/** Recadre une image au centre, en carré de 256 px (le cercle est fait à l'affichage), en JPEG. */
export async function cropPhoto(file: File): Promise<string> {
  if (!["image/jpeg", "image/png"].includes(file.type)) throw new Error("Choisis une image JPG ou PNG.");
  if (file.size > PHOTO_MAX_BYTES) throw new Error("L’image dépasse 5 Mo.");
  const bitmap = await createImageBitmap(file);
  const side = Math.min(bitmap.width, bitmap.height);
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = 256;
  const context = canvas.getContext("2d");
  if (!context) throw new Error("Impossible de lire cette image.");
  context.drawImage(bitmap, (bitmap.width - side) / 2, (bitmap.height - side) / 2, side, side, 0, 0, 256, 256);
  return canvas.toDataURL("image/jpeg", 0.86);
}

export function useProfileImage() {
  const { me } = useAuth();
  const name = computed(() => fullName.value || me.value?.username || "");
  const firstName = computed(() => name.value.trim().split(/\s+/)[0] ?? "");
  const initials = computed(() => initialsOf(name.value) || "?");
  const choice = computed<ImageChoice>(() => {
    if (photo.value) return { kind: "photo", src: photo.value };
    if (avatar.value) return { kind: "avatar", avatar: avatar.value };
    return { kind: "initials" };
  });

  async function load(force = false): Promise<void> {
    const account = me.value?.authenticated ? (me.value.username ?? null) : null;
    if (account !== loadedFor) forgetProfileImage();
    if (loading && !force) return loading;
    loadedFor = account;
    photo.value = readPhoto(account);
    loading = (async () => {
      const [image, identity] = await Promise.all([
        api.GET("/api/profile-image").catch(() => ({ data: undefined })),
        api.GET("/api/identity").catch(() => ({ data: undefined })),
      ]);
      avatar.value = image.data?.avatar ?? null;
      fullName.value = identity.data?.name ?? null;
      email.value = identity.data?.email?.trim() || null;
      city.value = identity.data?.city?.trim() || null;
    })();
    return loading;
  }

  // Enregistrer : un avatar va au serveur et efface la photo locale ; une photo reste locale et retire l'avatar.
  async function save(next: ImageChoice): Promise<void> {
    const wanted = next.kind === "avatar" ? next.avatar : null;
    await api.PUT("/api/profile-image", { body: { avatar: wanted } });
    avatar.value = wanted;
    photo.value = next.kind === "photo" ? next.src : null;
    writePhoto(loadedFor, photo.value);
  }

  return { choice, initials, name, firstName, email, city, avatar, photo, load, save };
}
