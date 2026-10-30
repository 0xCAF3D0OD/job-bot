"""Lettre de motivation : rédaction par l'IA, versions, relecture, export Word (docs/08 §3).

Les coordonnées de Kevin ne partent jamais vers l'IA : elles sont ajoutées par
`letters.document.assemble`, à l'affichage comme dans le Word.
"""

from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated, Any, Literal
from urllib.parse import quote
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.api.routes import writing
from jobbot.db.models import Application, Draft, DraftKind, ForbiddenClaim, Offer
from jobbot.letters.document import Identity, LetterDocument, Recipient, assemble, to_docx
from jobbot.letters.pdf import letter_to_pdf
from jobbot.letters.service import load_identity
from jobbot.llm import claims as claims_check
from jobbot.llm import letter as letter_llm
from jobbot.llm import letter_review
from jobbot.llm.scoring import InvalidScore
from jobbot.log import get_logger
from jobbot.runtime import Runtime

router = APIRouter(prefix="/api", tags=["letters"])
log = get_logger(__name__)
LOCAL_TZ = ZoneInfo("Europe/Zurich")
# Estimation prudente d'une rédaction (docs/08 §6), pour ne pas dépasser le plafond.
LETTER_ESTIMATE_USD = Decimal("0.10")
Language = Literal["fr", "en", "de"]
DOCX_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


class LetterParagraph(BaseModel):
    text: Annotated[str, Field(min_length=1, max_length=4000)]
    chunk_ids: list[int] = Field(default_factory=list)


class EmployerOut(BaseModel):
    address: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None


class LetterDocumentOut(BaseModel):
    """La lettre telle qu'elle sera envoyée, en-tête compris."""

    model_config = ConfigDict(from_attributes=True)

    language: Language
    sender: list[str]
    place_date: str
    recipient: list[str]
    subject_line: str
    salutation: str
    paragraphs: list[str]
    closing: str
    signature: str
    enclosure: str
    # Coordonnées manquantes dans les Réglages (en-tête incomplet).
    missing_identity: list[str]


class ReviewCriterionOut(BaseModel):
    key: str
    label: str
    ok: bool
    reason: str


class ReviewOut(BaseModel):
    """La relecture avant affichage : sept critères, réussis ou à revoir."""

    criteria: list[ReviewCriterionOut]
    # Une correction automatique a été faite (au plus une).
    corrected: bool


class LetterOut(BaseModel):
    id: int
    offer_id: int
    version: int
    language: Language
    subject: str
    paragraphs: list[LetterParagraph]
    employer: EmployerOut
    instruction: str | None
    model: str | None
    created_at: datetime
    edited_at: datetime | None
    document: LetterDocumentOut
    # Absente tant que la lettre n'est pas relue (ou pour une lettre d'avant la relecture).
    review: ReviewOut | None = None


class LetterRequest(BaseModel):
    # None : langue de l'annonce.
    language: Language | None = None
    # Consigne pour une nouvelle version (« plus court », « insiste sur Kubernetes »).
    instruction: Annotated[str, Field(max_length=500)] | None = None
    # Version à retravailler ; par défaut la plus récente.
    base_draft_id: int | None = None


class FalseClaimIn(BaseModel):
    """« Pas vrai » sur une phrase de la lettre : la retirer, ou la réécrire d'après le profil."""

    sentence: Annotated[str, Field(min_length=3, max_length=2000)]
    mode: Literal["remove", "rewrite"] = "remove"


class FalseClaimOut(BaseModel):
    # La version corrigée : la même (phrase retirée) ou une nouvelle (réécrite).
    letter: LetterOut
    # L'affirmation ajoutée aux interdits, pour « Annuler ».
    claim_id: int


class ForbiddenClaimOut(BaseModel):
    id: int
    text: str
    created_at: datetime


class LetterEdit(BaseModel):
    subject: Annotated[str, Field(min_length=1, max_length=200)]
    paragraphs: list[LetterParagraph] = Field(min_length=1, max_length=10)
    language: Language | None = None


async def _recipient(session: AsyncSession, offer: Offer, draft: Draft) -> Recipient:
    """La candidature enregistrée fait foi ; sinon l'offre et ce que l'IA a relevé."""
    application = await session.scalar(select(Application).where(Application.offer_id == offer.id))
    if application is not None:
        return Recipient(application.company, application.company_address, application.contact_name)
    employer = draft.content.get("employer") or {}
    address = offer.company_address or employer.get("address")
    return Recipient(offer.company, address, employer.get("contact_name"))


def _document(identity: Identity, recipient: Recipient, draft: Draft) -> LetterDocument:
    day = (draft.edited_at or draft.created_at).astimezone(LOCAL_TZ).date()
    return assemble(
        identity,
        recipient,
        draft.language,
        letter_llm.no_dash(draft.content["subject"]),
        [letter_llm.no_dash(p["text"]) for p in draft.content["paragraphs"]],
        day,
        salutation=draft.content.get("salutation"),
        closing=draft.content.get("closing"),
    )


def _out(draft: Draft, document: LetterDocument) -> LetterOut:
    return LetterOut(
        id=draft.id,
        offer_id=draft.offer_id,
        version=draft.version,
        language=draft.language,
        # Le texte rendu, sans tiret cadratin, même pour une lettre d'avant le garde-fou.
        subject=letter_llm.no_dash(draft.content["subject"]),
        paragraphs=[
            LetterParagraph(**{**p, "text": letter_llm.no_dash(p["text"])})
            for p in draft.content["paragraphs"]
        ],
        employer=EmployerOut(**(draft.content.get("employer") or {})),
        instruction=draft.instruction,
        model=draft.model,
        created_at=draft.created_at,
        edited_at=draft.edited_at,
        document=LetterDocumentOut(**asdict(document)),
        review=_review_out(draft.content.get("review")),
    )


def _review_out(review: dict[str, Any] | None) -> ReviewOut | None:
    if not review:
        return None
    return ReviewOut(
        criteria=[ReviewCriterionOut(**c) for c in review.get("criteria", [])],
        corrected=bool(review.get("corrected")),
    )


async def _render(session: AsyncSession, draft: Draft) -> LetterOut:
    offer = await session.get(Offer, draft.offer_id)
    assert offer is not None  # suppression en cascade
    identity = await load_identity(session)
    return _out(draft, _document(identity, await _recipient(session, offer, draft), draft))


async def _get_draft(session: AsyncSession, draft_id: int) -> Draft:
    return await writing.get_draft(session, draft_id, DraftKind.LETTER)


@router.get("/offers/{offer_id}/letters", operation_id="listLetters")
async def list_letters(request: Request, offer_id: int) -> list[LetterOut]:
    """Toutes les versions, la plus récente d'abord."""
    async with _runtime(request).sessionmaker() as session:
        if await session.get(Offer, offer_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "offre introuvable")
        drafts = await session.scalars(
            select(Draft)
            .where(Draft.offer_id == offer_id, Draft.kind == DraftKind.LETTER)
            .order_by(Draft.version.desc())
        )
        return [await _render(session, d) for d in drafts]


@router.post(
    "/offers/{offer_id}/letters",
    operation_id="writeLetter",
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {
            "description": "IA non configurée, profil vide, budget atteint ou compte indisponible"
        },
        422: {
            "description": "Consigne hors de portée (coordonnées, date…) ou sans effet : "
            "aucune version créée, le message le dit"
        },
        502: {"description": "Réponse de l'IA inutilisable"},
        503: {"description": "IA momentanément indisponible"},
    },
)
async def write_letter(request: Request, offer_id: int, body: LetterRequest) -> LetterOut:
    """L'IA rédige une nouvelle version (quelques dizaines de secondes)."""
    instruction = (body.instruction or "").strip() or None
    return await _write(
        _runtime(request),
        offer_id,
        language=body.language,
        base_draft_id=body.base_draft_id,
        instruction=instruction,
    )


async def _write(
    runtime: Runtime,
    offer_id: int,
    *,
    language: letter_llm.Language | None,
    base_draft_id: int | None,
    instruction: str | None,
    saved_instruction: str | None = None,
) -> LetterOut:
    """Une nouvelle version. `saved_instruction` : ce que la version montre comme consigne, quand
    elle diffère de celle donnée à l'IA (« Pas vrai : … »)."""
    settings = runtime.settings
    ctx = await writing.prepare(
        runtime,
        offer_id,
        DraftKind.LETTER,
        base_draft_id=base_draft_id,
        instruction=instruction,
        estimate_usd=LETTER_ESTIMATE_USD,
    )
    params = letter_llm.request_params(
        settings.llm_model,
        settings.llm_writing_effort,
        ctx.chunks,
        ctx.offer,
        language=language,
        assessment=ctx.assessment,
        previous=ctx.previous,
        instruction=instruction,
        forbidden=ctx.forbidden,
    )
    raw = await writing.call(
        runtime, params, offer_id=offer_id, kind=DraftKind.LETTER, rate=ctx.rate
    )
    try:
        output = letter_llm.parse_output(raw.text, ctx.chunks)
    except InvalidScore:
        raise writing.unusable() from None
    # Une demande hors de portée (coordonnées, date, destinataire) : une ligne, pas de version.
    if output.refusal:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, output.refusal)
    content = output.model_dump(exclude={"language", "refusal"})
    # Une version identique à celle d'où elle part : rien à créer.
    if (
        ctx.previous is not None
        and ctx.previous_language == output.language
        and _same_letter(ctx.previous, content)
    ):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Cette consigne ne change rien à la lettre : pas de nouvelle version.",
        )

    async with runtime.sessionmaker.begin() as session:
        draft = await writing.add_version(
            session,
            offer_id,
            DraftKind.LETTER,
            language=output.language,
            content=content,
            instruction=saved_instruction or instruction,
            model=raw.model,
            prompt_version=letter_llm.PROMPT_VERSION,
        )
        offer = await session.get(Offer, offer_id)
        if offer is not None and offer.company_address is None and output.employer.address:
            # Dernier recours (docs/12 §2.3) : l'adresse relevée dans l'annonce par l'IA.
            offer.company_address = output.employer.address
            offer.company_address_source = "letter"
        out = await _render(session, draft)
    log.info("letter_written", offer_id=offer_id, version=out.version, language=out.language)
    return out


def _same_letter(previous: dict[str, Any], content: dict[str, Any]) -> bool:
    """Même objet, mêmes formules, même corps (aux espaces près)."""

    def norm(letter: dict[str, Any]) -> tuple[str, ...]:
        parts = [
            letter.get("subject") or "",
            letter.get("salutation") or "",
            letter.get("closing") or "",
        ]
        parts += [p["text"] for p in letter.get("paragraphs", [])]
        return tuple(" ".join(part.split()) for part in parts)

    base = dict(previous)
    # Une ancienne version sans formules avait celles de la langue.
    base.setdefault("salutation", content.get("salutation"))
    base.setdefault("closing", content.get("closing"))
    return norm(base) == norm(content)


def _flags(ctx: writing.WritingContext, letter: dict[str, Any]) -> list[claims_check.Flag]:
    """Les phrases plus fortes que leur source, ou marquées « Pas vrai » (sans l'IA)."""
    return claims_check.check(
        letter, ctx.chunks, offer_text=ctx.offer.text or "", forbidden=ctx.forbidden
    )


async def _reviewed(
    runtime: Runtime,
    ctx: writing.WritingContext,
    letter: dict[str, Any],
    *,
    offer_id: int,
    language: str,
    instruction: str | None,
    corrected: bool = False,
) -> letter_review.Review:
    settings = runtime.settings
    flags = _flags(ctx, letter)
    params = letter_review.request_params(
        settings.llm_model,
        settings.llm_writing_effort,
        ctx.chunks,
        ctx.offer,
        letter,
        language=language,
        instruction=instruction,
        flags=flags,
        forbidden=ctx.forbidden,
    )
    raw = await writing.call(
        runtime, params, offer_id=offer_id, kind=DraftKind.LETTER, rate=ctx.rate
    )
    try:
        return letter_review.parse_review(raw.text, letter, corrected=corrected, flags=flags)
    except InvalidScore:
        raise writing.unusable() from None


@router.post(
    "/letters/{draft_id}/review",
    operation_id="reviewLetter",
    responses={
        409: {"description": "IA non configurée, profil vide ou budget atteint"},
        502: {"description": "Réponse de l'IA inutilisable"},
        503: {"description": "IA momentanément indisponible"},
    },
)
async def review_letter(request: Request, draft_id: int) -> LetterOut:
    """Relecture avant affichage : une relecture, au plus une correction, puis une relecture.

    Chaque phrase est rapprochée de sa source (30.10.2026) : une affirmation plus forte que son
    bloc est réécrite au niveau du bloc par le relecteur, ou retirée. Ce que le contrôle sans l'IA
    signale encore à la fin est retiré : une lettre affichée ne dit jamais plus que le profil.
    """
    runtime = _runtime(request)
    settings = runtime.settings
    async with runtime.sessionmaker() as session:
        draft = await _get_draft(session, draft_id)
        offer_id, language, instruction = draft.offer_id, draft.language, draft.instruction
        letter = {k: v for k, v in draft.content.items() if k != "review"}
    ctx = await writing.prepare(
        runtime,
        offer_id,
        DraftKind.LETTER,
        base_draft_id=draft_id,
        instruction=instruction,
        estimate_usd=LETTER_ESTIMATE_USD,
        check_plan=False,
    )
    review = await _reviewed(
        runtime, ctx, letter, offer_id=offer_id, language=language, instruction=instruction
    )
    letter = letter_review.apply_claims(letter, review)
    fixed_claims = len(review.claims)
    if not review.all_ok:
        # Une seule correction automatique, puis une nouvelle relecture : jamais de boucle.
        params = letter_llm.request_params(
            settings.llm_model,
            settings.llm_writing_effort,
            ctx.chunks,
            ctx.offer,
            language=language,  # type: ignore[arg-type]
            assessment=ctx.assessment,
            previous=letter,
            instruction=letter_review.correction_instruction(review),
            forbidden=ctx.forbidden,
        )
        raw = await writing.call(
            runtime, params, offer_id=offer_id, kind=DraftKind.LETTER, rate=ctx.rate
        )
        try:
            fixed = letter_llm.parse_output(raw.text, ctx.chunks)
        except InvalidScore:
            fixed = None
        if fixed is not None and not fixed.refusal:
            letter = {**letter, **fixed.model_dump(exclude={"language", "refusal", "employer"})}
            review = await _reviewed(
                runtime,
                ctx,
                letter,
                offer_id=offer_id,
                language=language,
                instruction=instruction,
                corrected=True,
            )
            letter = letter_review.apply_claims(letter, review)
            fixed_claims += len(review.claims)
    # Ce qui reste plus fort que le profil est retiré ; « Aucune invention » le dit.
    remaining = _flags(ctx, letter)
    if remaining:
        letter = claims_check.drop(letter, remaining)
    if fixed_claims or remaining:
        count = fixed_claims + len(remaining)
        plural = "s" if count > 1 else ""
        reason = (
            f"{count} phrase{plural} plus forte{plural} que ton profil, "
            f"corrigée{plural} ou retirée{plural}."
        )
        review = letter_review.Review(
            [
                letter_review.Criterion(c.key, c.label, True, reason)
                if c.key == "invention" and not _flags(ctx, letter)
                else c
                for c in review.criteria
            ],
            review.claims,
            corrected=True,
        )
    async with runtime.sessionmaker.begin() as session:
        draft = await _get_draft(session, draft_id)
        draft.content = {**letter, "review": review.as_dict()}
        await session.flush()
        await session.refresh(draft)
        out = await _render(session, draft)
    log.info(
        "letter_reviewed",
        offer_id=offer_id,
        passed=review.passed,
        total=len(review.criteria),
        corrected=review.corrected,
        claims=fixed_claims,
        removed=len(remaining),
    )
    return out


def _without(letter: dict[str, Any], sentence: str) -> dict[str, Any] | None:
    """La lettre sans cette phrase (aux espaces près) ; None si elle n'y est pas."""
    wanted = " ".join(sentence.split())
    paragraphs = []
    found = False
    for paragraph in letter.get("paragraphs", []):
        text = " ".join(paragraph["text"].split())
        if not found and wanted in text:
            found = True
            text = " ".join(text.replace(wanted, " ").split())
        if text:
            paragraphs.append({**paragraph, "text": text})
    if not found:
        return None
    return {**letter, "paragraphs": paragraphs}


@router.post(
    "/letters/{draft_id}/false-claim",
    operation_id="markFalseClaim",
    responses={
        404: {"description": "Lettre introuvable"},
        409: {"description": "Réécrire : IA non configurée, profil vide ou budget atteint"},
        422: {"description": "Phrase introuvable dans cette version, ou seule phrase de la lettre"},
    },
)
async def mark_false_claim(request: Request, draft_id: int, body: FalseClaimIn) -> FalseClaimOut:
    """« Pas vrai » : la phrase rejoint les interdits du profil, puis elle est retirée de cette
    version, ou réécrite d'après le profil dans une nouvelle version."""
    runtime = _runtime(request)
    sentence = " ".join(body.sentence.split())
    async with runtime.sessionmaker.begin() as session:
        draft = await _get_draft(session, draft_id)
        offer_id, language = draft.offer_id, draft.language
        without = _without(draft.content, sentence)
        if without is None:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, "Phrase introuvable dans cette version."
            )
        if body.mode == "remove" and not without["paragraphs"]:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                "C'est la seule phrase de la lettre : rédige plutôt une nouvelle version.",
            )
        claim = ForbiddenClaim(text=sentence, draft_id=draft_id)
        session.add(claim)
        await session.flush()
        claim_id = claim.id
        if body.mode == "remove":
            draft.content = without
            draft.edited_at = datetime.now(UTC)
            await session.flush()
            await session.refresh(draft)
            out = await _render(session, draft)
    if body.mode == "rewrite":
        out = await _write(
            runtime,
            offer_id,
            language=language,  # type: ignore[arg-type]
            base_draft_id=draft_id,
            instruction=(
                f"Cette phrase est fausse : « {sentence} ». Réécris-la au niveau exact de ce que "
                "disent les blocs du profil, ou retire-la s'ils n'en disent rien. Ne change rien "
                "d'autre."
            ),
            saved_instruction=f"Pas vrai : « {sentence} »"[:500],
        )
    log.info("letter_false_claim", draft_id=draft_id, mode=body.mode)
    return FalseClaimOut(letter=out, claim_id=claim_id)


@router.get("/forbidden-claims", operation_id="listForbiddenClaims")
async def list_forbidden_claims(request: Request) -> list[ForbiddenClaimOut]:
    """Les affirmations marquées « Pas vrai », les plus récentes d'abord."""
    async with _runtime(request).sessionmaker() as session:
        rows = await session.scalars(select(ForbiddenClaim).order_by(ForbiddenClaim.id.desc()))
        return [ForbiddenClaimOut(id=c.id, text=c.text, created_at=c.created_at) for c in rows]


@router.delete(
    "/forbidden-claims/{claim_id}",
    operation_id="deleteForbiddenClaim",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_forbidden_claim(request: Request, claim_id: int) -> Response:
    """« Annuler », ou l'affirmation était vraie finalement : elle n'est plus interdite."""
    async with _runtime(request).sessionmaker.begin() as session:
        claim = await session.get(ForbiddenClaim, claim_id)
        if claim is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "affirmation introuvable")
        await session.delete(claim)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/letters/{draft_id}", operation_id="editLetter")
async def edit_letter(request: Request, draft_id: int, body: LetterEdit) -> LetterOut:
    """Corrections de Kevin : la version modifiée devient celle qui compte."""
    async with _runtime(request).sessionmaker.begin() as session:
        draft = await _get_draft(session, draft_id)
        draft.content = {
            **draft.content,
            "subject": body.subject.strip(),
            "paragraphs": [
                {"text": p.text.strip(), "chunk_ids": p.chunk_ids}
                for p in body.paragraphs
                if p.text.strip()
            ],
        }
        if body.language:
            draft.language = body.language
        draft.edited_at = datetime.now(UTC)
        await session.flush()
        await session.refresh(draft)
        return await _render(session, draft)


@router.get(
    "/letters/{draft_id}/docx",
    operation_id="downloadLetterDocx",
    response_class=Response,
    responses={200: {"content": {DOCX_TYPE: {}}}},
)
async def download_letter_docx(request: Request, draft_id: int) -> Response:
    async with _runtime(request).sessionmaker() as session:
        draft = await _get_draft(session, draft_id)
        offer = await session.get(Offer, draft.offer_id)
        assert offer is not None
        document = _document(
            await load_identity(session), await _recipient(session, offer, draft), draft
        )
    company = "".join(c for c in (offer.company or "employeur") if c.isalnum() or c in " -")
    filename = f"Lettre - {company.strip()[:60]}.docx"
    return Response(
        to_docx(document),
        media_type=DOCX_TYPE,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )


@router.get(
    "/letters/{draft_id}/pdf",
    operation_id="downloadLetterPdf",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}}},
)
async def download_letter_pdf(request: Request, draft_id: int) -> Response:
    """La même lettre en PDF, à joindre aux formulaires en ligne (docs/25 §3.4)."""
    async with _runtime(request).sessionmaker() as session:
        draft = await _get_draft(session, draft_id)
        offer = await session.get(Offer, draft.offer_id)
        assert offer is not None
        document = _document(
            await load_identity(session), await _recipient(session, offer, draft), draft
        )
    company = "".join(c for c in (offer.company or "employeur") if c.isalnum() or c in " -")
    filename = f"Lettre - {company.strip()[:60]}.pdf"
    return Response(
        letter_to_pdf(document, title=filename[:-4]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )
