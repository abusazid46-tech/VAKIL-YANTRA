from __future__ import annotations

import json
from uuid import uuid4

from sqlalchemy.orm import Session

from app.db.models import AiRun
from app.domain.ai.rag_service import (
    build_statutory_grounding_prompt,
    retrieve_statutory_citations,
)
from app.domain.ai.schemas import AiResponse, CaseAnalysisRequest, Citation, DraftRequest
from app.domain.auth.schemas import CurrentUser
from app.integrations.model_gateway import get_model_gateway

_warning = "AI output is assistive only. Verify every fact, citation, statute, procedure and date before submission to court."


def create_draft(db: Session, user: CurrentUser, payload: DraftRequest) -> AiResponse:
    # 1. RAG Retrieval from Statutory Corpus
    query_text = f"{payload.document_type} {payload.sections or ''} {payload.court} {payload.facts}"
    citations = retrieve_statutory_citations(db, query_text, limit=4)
    statutory_context = build_statutory_grounding_prompt(citations)

    # 2. Model Prompt Preparation
    system_instruction = (
        "You are an expert Indian advocate assistant. Generate a formal, court-ready legal draft "
        "following standard Indian High Court and District Court conventions. "
        "Incorporate the provided statutory provisions accurately and cite the Sections explicitly."
    )
    user_prompt = (
        f"Document Type: {payload.document_type}\n"
        f"Court: {payload.court}\n"
        f"Client: {payload.client_name or 'Applicant'}\n"
        f"Statutory Sections: {payload.sections or 'Applicable statutory provisions'}\n"
        f"Case Facts: {payload.facts}\n"
    )

    # 3. Model Generation (Gemini / OpenAI / Grounded Synthesizer)
    gateway = get_model_gateway()
    generated_text = gateway.generate_legal_text(system_instruction, user_prompt, statutory_context)

    # 4. Fallback/Template Enhancement if local
    final_draft = _assemble_court_draft(payload, generated_text, citations)

    response = AiResponse(
        run_id=f"airun_{uuid4().hex[:12]}",
        status="completed",
        output={
            "title": f"{payload.document_type} - {payload.court}",
            "draft": final_draft,
            "next_steps": [
                f"Verify service proof and file vakalatnama in {payload.court}",
                "Attach certified copies of impugned order or FIR",
                "Ensure compliance with High Court / District Court practice rules",
                "Calculate limitation and delay condonation if required",
            ],
            "statutory_provisions": [c.title for c in citations],
        },
        citations=citations,
        verification_warning=_warning,
    )
    persist_ai_run(db, user, "draft", response)
    return response


def analyse_case(db: Session, user: CurrentUser, payload: CaseAnalysisRequest) -> AiResponse:
    # 1. RAG Retrieval from Statutory Corpus
    citations = retrieve_statutory_citations(db, payload.facts, limit=4)
    
    # 2. Extract statutory ingredients from retrieved citations
    ingredients = [
        f"Statutory element: {c.title} ({c.snippet[:120]}...)"
        for c in citations
    ] or ["Review foundational statutory ingredients under applicable enactments"]

    response = AiResponse(
        run_id=f"airun_{uuid4().hex[:12]}",
        status="completed",
        output={
            "action_steps": [
                "Review evidentiary chain of custody and certified FIR / petition copies",
                "Map recorded facts against statutory thresholds in retrieved Central Acts",
                "Draft preliminary objection matrix or bail ground checklist",
                "Cross-check filing timelines with the Limitation Act, 1963",
            ],
            "argument_preparation": [
                f"Perspective: Acting for {payload.advocate_role.upper()}",
                "Scrutinize non-compliance with statutory notice periods and mandatory procedures",
                "Highlight parity of co-accused, absence of flight risk, and roots in society",
                "Prepare targeted counter-arguments against mechanical detention",
            ],
            "procedural_guidance": [
                "Verify territorial and pecuniary jurisdiction of the forum",
                "Ensure Section 61 BSA certificate is attached for all electronic evidence",
                "Check for court vacation schedules or limitation exclusion under Section 12",
            ],
            "statutory_ingredients": ingredients,
        },
        citations=citations,
        verification_warning=_warning,
    )
    persist_ai_run(db, user, "case_analysis", response)
    return response


def _assemble_court_draft(payload: DraftRequest, generated_text: str, citations: list[Citation]) -> str:
    court_upper = payload.court.upper()
    doc_type_upper = payload.document_type.upper()
    client = payload.client_name or "Applicant"
    sections_str = payload.sections or "the relevant provisions of law"

    citation_summary = "\n".join([f"  • {c.title}: {c.snippet[:160]}..." for c in citations])

    return f"""IN THE {court_upper}

IN THE MATTER OF:
{client}
... {payload.document_type.split()[0]} / Petitioner

VERSUS

State / Respondent

{doc_type_upper} UNDER {sections_str.upper()}

MOST RESPECTFULLY SHOWETH:

1. That the applicant/petitioner has approached this Hon'ble Court seeking {payload.document_type} on the following factual and legal premises:
   {payload.facts}

2. STATUTORY GROUNDING & INGREDIENTS:
{citation_summary if citations else "   • Governed by statutory provisions of applicable Indian Central Acts."}

3. GROUNDS:
   A. That the applicant is innocent and has been falsely implicated without prima facie corroboration.
   B. That the custodial interrogation of the applicant is no longer required and no recovery is pending.
   C. That the applicant is a respectable citizen with deep roots in society and undertakes to strictly abide by all terms and conditions imposed by this Hon'ble Court.
   D. That the applicant undertakes not to tamper with prosecution evidence, tamper with witness testimonies, or flee from the jurisdiction of this Court.

PRAYER:
Wherefore, in the facts and circumstances of the case, it is most respectfully prayed that this Hon'ble Court may be pleased to:
(a) Grant {payload.document_type.lower()} to the applicant on such terms and conditions as this Hon'ble Court deems fit and proper;
(b) Pass any other or further order(s) as this Hon'ble Court may deem fit in the interest of justice and equity.

AND FOR THIS ACT OF KINDNESS, THE APPLICANT AS IN DUTY BOUND SHALL EVER PRAY.

Filed by:
Advocate for the Applicant
Place: High Court / District Court
Date: 2026
"""


def persist_ai_run(db: Session, user: CurrentUser, run_type: str, response: AiResponse) -> None:
    db.add(
        AiRun(
            id=response.run_id,
            firm_id=user.firm_id,
            actor_user_id=user.user_id,
            run_type=run_type,
            output_json=json.dumps(response.model_dump(mode="json")),
        )
    )
    db.commit()
