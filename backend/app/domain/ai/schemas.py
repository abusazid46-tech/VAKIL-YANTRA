from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field, model_validator


class Citation(BaseModel):
    citation_id: str = ""
    source_id: str = ""
    source_title: str
    title: str = ""
    section_number: str | None = None
    heading: str | None = None
    quote_excerpt: str = ""
    snippet: str = ""
    similarity_score: float = 1.0
    source_url: str = ""
    url: str = ""
    chunk_type: str = "section"

    @model_validator(mode="before")
    @classmethod
    def sync_citation_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "source_id" in data and not data.get("citation_id"):
                data["citation_id"] = data["source_id"]
            if "citation_id" in data and not data.get("source_id"):
                data["source_id"] = data["citation_id"]
            if "title" in data and not data.get("source_title"):
                data["source_title"] = data["title"]
            if "source_title" in data and not data.get("title"):
                data["title"] = data["source_title"]
            if "snippet" in data and not data.get("quote_excerpt"):
                data["quote_excerpt"] = data["snippet"]
            if "quote_excerpt" in data and not data.get("snippet"):
                data["snippet"] = data["quote_excerpt"]
            if "url" in data and not data.get("source_url"):
                data["source_url"] = data["url"]
            if "source_url" in data and not data.get("url"):
                data["url"] = data["source_url"]
        return data


class DraftRequest(BaseModel):
    matter_id: str | None = None
    document_type: str = "Bail Application"
    court: str = "High Court / District Court"
    client_name: str | None = None
    sections: str | None = None
    facts: str = Field(default="")

    @model_validator(mode="before")
    @classmethod
    def normalize_draft_inputs(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "draft_type" in data and not data.get("document_type"):
                data["document_type"] = data["draft_type"]
            if "jurisdiction" in data and not data.get("court"):
                data["court"] = data["jurisdiction"]
            if "fact_summary" in data and not data.get("facts"):
                data["facts"] = data["fact_summary"]
            if "statutory_hints" in data and not data.get("sections"):
                data["sections"] = data["statutory_hints"]
            if "matter_title" in data and not data.get("client_name"):
                data["client_name"] = data["matter_title"]
        return data


class CaseAnalysisRequest(BaseModel):
    document_id: str | None = None
    advocate_role: str = "Defence Counsel"
    matter_id: str | None = None
    matter_title: str | None = None
    case_notes: str | None = None
    allegations: str | None = None
    relief_sought: str | None = None
    facts: str = Field(default="")

    @model_validator(mode="before")
    @classmethod
    def normalize_case_inputs(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("facts"):
                parts = []
                if data.get("matter_title"):
                    parts.append(f"Matter: {data['matter_title']}")
                if data.get("case_notes"):
                    parts.append(f"Case Notes: {data['case_notes']}")
                if data.get("allegations"):
                    parts.append(f"Allegations: {data['allegations']}")
                if data.get("relief_sought"):
                    parts.append(f"Relief Sought: {data['relief_sought']}")
                data["facts"] = "\n".join(parts) or "Review of case facts and statutory ingredients"
        return data


class AiResponse(BaseModel):
    run_id: str
    status: str = "completed"
    output_text: str = ""
    draft_type: str | None = None
    output: dict[str, object] = Field(default_factory=dict)
    citations: list[Citation] = Field(default_factory=list)
    verification_warning: str = ""
    retrieved_context_count: int = 0

    @model_validator(mode="before")
    @classmethod
    def sync_response_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            out = data.get("output", {})
            if isinstance(out, dict):
                if not data.get("output_text"):
                    data["output_text"] = str(out.get("draft") or out.get("analysis") or "")
            elif isinstance(out, str) and not data.get("output_text"):
                data["output_text"] = out
            if "citations" in data and not data.get("retrieved_context_count"):
                data["retrieved_context_count"] = len(data["citations"])
        return data
