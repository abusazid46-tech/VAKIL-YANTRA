from pydantic import BaseModel


class LegalSource(BaseModel):
    id: str
    title: str
    source_type: str
    jurisdiction: str
    year: int
    public_url: str
    effective_status: str
    act_number: str | None = None
    enactment_date: str | None = None


class LegalSearchResponse(BaseModel):
    query: str
    results: list[LegalSource]

