import { flushPromises, type VueWrapper } from "@vue/test-utils";

// Choisir un jour dans un DateField comme le ferait la personne : la pilule, la saisie jj.mm.aaaa, « Valider ».
export async function pickDate(wrapper: VueWrapper, testId: string, day: string): Promise<void> {
  await wrapper.find(`[data-test=${testId}] [data-test=dt-date]`).trigger("click");
  const typed = wrapper.find(`[data-test=${testId}] [data-test=dt-typed-date]`);
  const [y, m, d] = day.split("-");
  await typed.setValue(`${d}.${m}.${y}`);
  await typed.trigger("change");
  await wrapper.find(`[data-test=${testId}] [data-test=dt-confirm]`).trigger("click");
  await flushPromises();
}
