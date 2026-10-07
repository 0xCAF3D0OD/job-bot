// Mise en forme des réponses de l'assistant (docs/24) : paragraphes, listes, gras et blocs
// à copier. Pas de HTML interprété : le texte est découpé puis affiché par le gabarit.

export type Inline = { text: string; bold: boolean };
export type Block =
  | { kind: "p"; lines: Inline[][] }
  | { kind: "list"; ordered: boolean; items: Inline[][] }
  | { kind: "code"; text: string };

const ITEM = /^\s*(?:[-*•]|(\d+)[.)])\s+(.*)$/;

export function inline(text: string): Inline[] {
  const parts = text.split("**");
  // Un « ** » orphelin (réponse en cours d'écriture) reste du texte simple.
  if (parts.length % 2 === 0) return [{ text: text.replaceAll("`", ""), bold: false }];
  return parts
    .map((part, index) => ({ text: part.replaceAll("`", ""), bold: index % 2 === 1 }))
    .filter((part) => part.text);
}

export function blocks(text: string): Block[] {
  const found: Block[] = [];
  const lines = text.replaceAll("\r", "").split("\n");
  const at = (i: number): string => lines[i] ?? "";
  const fence = (i: number): boolean => at(i).trim().startsWith("```");
  let index = 0;
  while (index < lines.length) {
    if (fence(index)) {
      const body: string[] = [];
      index += 1;
      while (index < lines.length && !fence(index)) {
        body.push(at(index));
        index += 1;
      }
      found.push({ kind: "code", text: body.join("\n").trim() });
      index += 1;
      continue;
    }
    if (!at(index).trim()) {
      index += 1;
      continue;
    }
    const item = ITEM.exec(at(index));
    if (item) {
      const ordered = item[1] !== undefined;
      const items: Inline[][] = [];
      for (let next: RegExpExecArray | null = item; next; next = ITEM.exec(at(index))) {
        items.push(inline((next[2] ?? "").replace(/^#+\s*/, "")));
        index += 1;
        if (index >= lines.length) break;
      }
      found.push({ kind: "list", ordered, items });
      continue;
    }
    const paragraph: Inline[][] = [];
    while (index < lines.length && at(index).trim() && !ITEM.exec(at(index)) && !fence(index)) {
      // Les titres markdown deviennent une ligne en gras.
      const heading = /^\s*#+\s+(.*)$/.exec(at(index));
      paragraph.push(heading ? [{ text: heading[1] ?? "", bold: true }] : inline(at(index)));
      index += 1;
    }
    found.push({ kind: "p", lines: paragraph });
  }
  return found;
}

export type StreamEvent = { event: string; data: Record<string, unknown> };

// Découpe un flux SSE : rend les événements complets et le reste à compléter.
export function readEvents(buffer: string): { events: StreamEvent[]; rest: string } {
  const chunks = buffer.replaceAll("\r\n", "\n").split("\n\n");
  const rest = chunks.pop() ?? "";
  const events: StreamEvent[] = [];
  for (const chunk of chunks) {
    let event = "message";
    const data: string[] = [];
    for (const line of chunk.split("\n")) {
      if (line.startsWith("event:")) event = line.slice(6).trim();
      else if (line.startsWith("data:")) data.push(line.slice(5).trimStart());
    }
    if (!data.length) continue;
    try {
      events.push({ event, data: JSON.parse(data.join("\n")) as Record<string, unknown> });
    } catch {
      // Morceau illisible : ignoré.
    }
  }
  return { events, rest };
}
