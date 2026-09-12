from uuid import uuid4
import json

from sqlalchemy.orm import Session

from app.db.models import AiRun
from app.domain.ai.schemas import AiResponse, CaseAnalysisRequest, Citation, DraftRequest
from app.domain.auth.schemas import CurrentUser

_warning = "AI output is assistive only. Verify every fact, citation, statute, procedure and date before use."


def create_draft(db: Session, user: CurrentUser, payload: DraftRequest) -> AiResponse:
    response = AiResponse(
        run_id=f"airun_{uuid4().hex[:12]}",
        status="completed",
        output={
            "title": payload.document_type,
            "draft": (
                f"Draft {payload.document_type} for {payload.court}. "
                f"Sections: {payload.sections or 'to be verified'}. Facts: {payload.facts}"
            ),
            "next_steps": ["Verify source law", "Attach matter documents", "Review limitation impact"],
        },
        citations=[demo_citation()],
        verification_warning=_warning,
    )
    persist_ai_run(db, user, "draft", response)
    return response


def analyse_case(db: Session, user: CurrentUser, payload: CaseAnalysisRequest) -> AiResponse:
    response = AiResponse(
        run_id=f"airun_{uuid4().hex[:12]}",
        status="completed",
        output={
            "action_steps": ["Review uploaded evidence", "Map facts to statutory ingredients", "Prepare filing checklist"],
            "argument_preparation": [f"Analyse from role: {payload.advocate_role}", "Identify weak facts and missing documents"],
            "procedural_guidance": ["Confirm court jurisdiction", "Check limitation through deterministic rules engine"],
        },
        citations=[demo_citation()],
        verification_warning=_warning,
    )
    persist_ai_run(db, user, "case_analysis", response)
    return response


def demo_citation() -> Citation:
    return Citation(
        source_id="src_limitation_1963",
        title="Limitation Act, 1963",
        snippet="Use only as a source pointer; final legal position must be reviewed.",
        url="https://www.indiacode.nic.in/",
    )


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
