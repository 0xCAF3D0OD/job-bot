import { afterEach, describe, expect, it, vi } from "vitest";

const identities: Record<string, { name: string; city: string; avatar: number | null }> = {
  kevin: { name: "Kevin Di Nocera", city: "Renens", avatar: 3 },
  nouveau: { name: "", city: "", avatar: null },
};
let current = "kevin";
vi.mock("../api/client", () => ({
  api: {
    GET: vi.fn(async (path: string) => {
      const who = identities[current]!;
      if (path === "/api/identity") return { data: { name: who.name || null, city: who.city || null, email: null } };
      return { data: { avatar: who.avatar } };
    }),
    PUT: vi.fn(async () => ({})),
  },
}));

import { useAuth } from "./useAuth";
import { forgetProfileImage, useProfileImage } from "./useProfileImage";

function signIn(username: string): void {
  current = username;
  useAuth().me.value = { authenticated: true, username, setup_needed: false, auth_enabled: true, is_owner: false, welcome: "done", demo: false };
}

// Incident du 2026-11-09 : un compte créé après celui de Kevin, sur le même navigateur, affichait son nom, sa
// ville et son image, gardés en mémoire et jamais relus.
describe("Image de profil : propre à chaque compte", () => {
  afterEach(() => {
    forgetProfileImage();
    localStorage.clear();
  });

  it("un autre compte relit son nom, sa ville et son image au lieu de garder ceux du précédent", async () => {
    signIn("kevin");
    const image = useProfileImage();
    await image.load();
    expect(image.name.value).toBe("Kevin Di Nocera");
    expect(image.city.value).toBe("Renens");
    expect(image.choice.value).toEqual({ kind: "avatar", avatar: 3 });

    signIn("nouveau");
    await image.load();
    expect(image.name.value).toBe("nouveau");
    expect(image.city.value).toBeNull();
    expect(image.choice.value).toEqual({ kind: "initials" });
  });

  it("la photo importée reste au compte qui l'a choisie", async () => {
    signIn("kevin");
    const image = useProfileImage();
    await image.load();
    await image.save({ kind: "photo", src: "data:image/jpeg;base64,KEVIN" });
    expect(image.choice.value).toEqual({ kind: "photo", src: "data:image/jpeg;base64,KEVIN" });

    signIn("nouveau");
    await image.load();
    expect(image.photo.value).toBeNull();

    signIn("kevin");
    await image.load();
    expect(image.photo.value).toBe("data:image/jpeg;base64,KEVIN");
  });

  it("l'ancienne photo, gardée sans compte, n'est montrée à personne et disparaît", async () => {
    localStorage.setItem("joba1.profile-photo", "data:image/jpeg;base64,ANCIENNE");
    signIn("nouveau");
    const image = useProfileImage();
    await image.load();
    expect(image.photo.value).toBeNull();
    expect(localStorage.getItem("joba1.profile-photo")).toBeNull();
  });
});
