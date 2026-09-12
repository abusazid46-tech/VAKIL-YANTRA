from pydantic import BaseModel


class LegalSource(BaseModel):
    id: str
    title: str
    source_type: str
    jurisdiction: str
    year: int
    public_url: str
    effective_status: str


class LegalSearchResponse(BaseModel):
    query: str
    results: list[LegalSource]

