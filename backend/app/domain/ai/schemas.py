from pydantic import BaseModel, Field


class Citation(BaseModel):
    source_id: str
    title: str
    snippet: str
    url: str


class DraftRequest(BaseModel):
    matter_id: str | None = None
    document_type: str
    court: str
    sections: str | None = None
    facts: str = Field(min_length=10)


class CaseAnalysisRequest(BaseModel):
    document_id: str
    advocate_role: str
    matter_id: str | None = None


class AiResponse(BaseModel):
    run_id: str
    status: str
    output: dict[str, object]
    citations: list[Citation]
    verification_warning: str

