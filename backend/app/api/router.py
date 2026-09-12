from fastapi import APIRouter

from app.api.routes import ai, auth, billing, documents, health, legal_content, limitation, matters, workspace

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(matters.router, prefix="/matters", tags=["matters"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(legal_content.router, prefix="/legal-content", tags=["legal-content"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(limitation.router, prefix="/limitation", tags=["limitation"])
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
api_router.include_router(workspace.router, prefix="/workspace", tags=["workspace"])

