// L'annonce de la page (docs/142 §3), passée telle quelle à l'onglet actif (`func`), seulement au
// clic de la personne : l'ouverture du panneau (`full` faux) ne lit que le titre, l'entreprise et le
// lieu, pour la carte « Annonce sur cette page » ; « Envoyer à jobA1 » (`full` vrai) lit aussi le
// texte de l'annonce. Rien d'autre : ni cookies, ni formulaires, ni autres onglets. Sur LinkedIn,
// seulement l'annonce ouverte, jamais un profil ni une liste.
// Une seule fonction, sans rien autour : elle est copiée dans la page.

function jobA1Annonce(full) {
  const MAX = 40000;
  const clean = (value) => (typeof value === "string" ? value.replace(/\s+/g, " ").trim() : "");
  const fromHtml = (value) => {
    if (typeof value !== "string") return "";
    const doc = new DOMParser().parseFromString(value, "text/html");
    for (const br of doc.querySelectorAll("br, p, li, div, h1, h2, h3, h4")) br.append(" ");
    return clean(doc.body.textContent);
  };
  const textOf = (el) => (el ? clean(el.innerText || el.textContent) : "");

  // LinkedIn : l'annonce ouverte (/jobs/view/123, ou ?currentJobId=123 dans la recherche).
  const url = new URL(location.href);
  if (/(^|\.)linkedin\.com$/.test(url.hostname)) {
    const id = url.pathname.match(/^\/jobs\/view\/(?:[^/]*-)?(\d+)/)?.[1] || url.searchParams.get("currentJobId");
    if (!id || !/^\d+$/.test(id)) return null;
    const pick = (selectors) => {
      for (const s of selectors) {
        const found = textOf(document.querySelector(s));
        if (found) return found;
      }
      return "";
    };
    const title = pick([".job-details-jobs-unified-top-card__job-title", ".jobs-unified-top-card__job-title", ".top-card-layout__title"]);
    if (!title) return null;
    const result = {
      kind: "linkedin",
      url: `https://www.linkedin.com/jobs/view/${id}/`,
      title,
      company: pick([".job-details-jobs-unified-top-card__company-name", ".jobs-unified-top-card__company-name", ".topcard__org-name-link"]),
      location: "",
    };
    if (full) result.text = pick(["#job-details", ".jobs-description__content", ".jobs-box__html-content", ".description__text"]).slice(0, MAX);
    return result;
  }

  const pageUrl = `${url.origin}${url.pathname}${url.search}`;

  // Le balisage JobPosting (schema.org), celui de Google Jobs.
  const postings = [];
  const walk = (node) => {
    if (!node || typeof node !== "object") return;
    if (Array.isArray(node)) return node.forEach(walk);
    const type = node["@type"];
    if (type === "JobPosting" || (Array.isArray(type) && type.includes("JobPosting"))) postings.push(node);
    if (node["@graph"]) walk(node["@graph"]);
  };
  for (const script of document.querySelectorAll('script[type="application/ld+json"]')) {
    try {
      walk(JSON.parse(script.textContent));
    } catch {
      // Balisage mal formé : ignoré.
    }
  }
  const posting = postings[0];
  if (posting) {
    const org = posting.hiringOrganization;
    const place = [posting.jobLocation].flat()[0]?.address;
    const result = {
      kind: "posting",
      url: pageUrl,
      title: clean(posting.title || posting.name),
      company: clean(typeof org === "string" ? org : org?.name),
      location: clean(typeof place === "string" ? place : place?.addressLocality),
    };
    if (result.title) {
      if (full) {
        result.text = fromHtml(posting.description);
        // Description trop courte : le texte principal, s'il en dit plus.
        const main = textOf(document.querySelector("main, article"));
        if (result.text.length < 200 && main.length > result.text.length) result.text = main;
        result.text = result.text.slice(0, MAX);
      }
      return result;
    }
  }

  // Sinon le texte principal, seulement sur une page qui ressemble à une annonce.
  const root = document.querySelector("main, article, [role=main]");
  const body = textOf(root);
  const looksLikeAd = /job|emploi|stelle|offre|offer|career|carri|karriere|poste|vacanc|annonce|position|inserat/i.test(url.pathname + url.search);
  if (!root || body.length < 200 || !looksLikeAd) return null;
  const heading = textOf(root.querySelector("h1")) || textOf(document.querySelector("h1"));
  const result = { kind: "text", url: pageUrl, title: heading.slice(0, 300), company: "", location: "" };
  if (full) result.text = body.slice(0, MAX);
  return result;
}

globalThis.jobA1Annonce = jobA1Annonce;
