from fastapi import APIRouter, HTTPException

from ai_agent.agent import SafetyAgent
from ai_agent.model_provider import DemoModelProvider, RemoteJsonModelProvider
from backend.app.core import config
from backend.app.schemas.requests import ChatRequest
from backend.app.services.classification import predict_category
from backend.app.services.rights import search_rights

router = APIRouter(tags=["chat"])


def _provider():
    if config.AI_PROVIDER == "remote_json":
        try:
            return RemoteJsonModelProvider(config.AI_API_URL, config.AI_API_KEY, config.AI_MODEL_NAME)
        except ValueError as exc:
            raise HTTPException(status_code=503, detail="Remote AI provider is not configured; use AI_PROVIDER=demo or set its environment variables.") from exc
    if config.AI_PROVIDER != "demo":
        raise HTTPException(status_code=503, detail="Unknown AI_PROVIDER. Use 'demo' or 'remote_json'.")
    return DemoModelProvider()


@router.post("/chat")
@router.post("/api/chat", include_in_schema=False)
async def chat(request: ChatRequest) -> dict:
    try:
        agent = SafetyAgent(_provider(), predict_category, search_rights)
        # The schema restricts history roles and each message size. Convert it
        # back to plain dictionaries for the provider interface.
        history = [item.model_dump() for item in request.history]
        return await agent.respond(request.message, history, request.jurisdiction)
    except HTTPException:
        raise
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail="Classifier model is unavailable for agent triage.") from exc
    except Exception as exc:
        # Avoid returning model/provider internals or user text in server error responses.
        raise HTTPException(status_code=502, detail="The assistant could not generate a response. Please try again.") from exc
