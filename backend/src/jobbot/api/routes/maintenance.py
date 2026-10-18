"""L'état de la maintenance (docs/79), lisible sans connexion : l'interface le sonde pendant
qu'elle montre sa page d'attente, et le rappelle à l'exploitant qui passe quand même."""

from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel

from jobbot import accounts
from jobbot.runtime import Runtime

router = APIRouter(prefix="/api", tags=["maintenance"])


class MaintenanceOut(BaseModel):
    active: bool
    reason: Literal["announced", "update"] | None
    # « lecture » : les invités consultent encore, sans enregistrer (docs/80).
    mode: Literal["complete", "lecture"]
    message: str | None
    # L'exploitant pendant une maintenance annoncée : il passe, les autres attendent.
    bypass: bool


@router.get("/maintenance", operation_id="getMaintenance")
async def get_maintenance(request: Request) -> MaintenanceOut:
    runtime: Runtime = request.app.state.runtime
    state, owner = await request.app.state.maintenance.state(runtime)
    bypass = state.reason == "announced" and owner is not None and accounts.current() == owner
    return MaintenanceOut(
        active=state.active,
        reason=state.reason,
        mode=state.mode,
        message=state.message,
        bypass=bypass,
    )
