from __future__ import annotations

from typing import Any
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


class StatutoryProvisionItem(BaseModel):
    id: str
    act_id: str
    act_title: str
    chapter: str | None = None
    section_number: str
    section_title: str
    content: str
    chunk_type: str = "section"
    source_url: str
    source_page: int | str = 1
    amendment_information: Any = None
    effective_date: str | None = None


class ProvisionSearchResponse(BaseModel):
    query: str
    total_matches: int
    page: int = 1
    page_size: int = 25
    results: list[StatutoryProvisionItem]


class ActDirectoryItem(BaseModel):
    id: str
    title: str
    act_number: str | None = None
    year: int
    total_sections: int = 0
    public_url: str
    source_type: str = "central_act"
    jurisdiction: str = "India"
