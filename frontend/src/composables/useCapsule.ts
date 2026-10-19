import { computed, inject, type InjectionKey, ref, type Ref } from "vue";

// La capsule qui se déroule (docs/91) : la cloche, le compte et ☰ s'ouvrent dans le même
// cadre, une seule chose à la fois. La capsule (HeaderCapsule) fournit cet état ; hors de la
// capsule (un test, un écran sans barre), chaque zone garde son propre état.
export type CapsuleZone = "bell" | "account" | "menu";

export interface Capsule {
  active: Ref<CapsuleZone | null>;
}

export const CAPSULE: InjectionKey<Capsule> = Symbol("capsule");
// Où les zones rendent leur contenu, dans la capsule.
export const CAPSULE_BODY = "#capsule-body";

export function useCapsuleZone(zone: CapsuleZone) {
  const capsule = inject(CAPSULE, null);
  const local = ref(false);
  const open = computed<boolean>({
    get: () => (capsule ? capsule.active.value === zone : local.value),
    set: (value) => {
      if (!capsule) {
        local.value = value;
      } else if (value) {
        capsule.active.value = zone;
      } else if (capsule.active.value === zone) {
        capsule.active.value = null;
      }
    },
  });
  return { open, inCapsule: capsule !== null };
}
