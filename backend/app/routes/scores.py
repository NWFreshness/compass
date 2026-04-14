import uuid
from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from app.db import get_db
from app.middleware.auth import get_current_user
from app.models import Score, User
from app.schemas.score import ScoreCreate, ScoreResponse, CSVImportResult
from app.services.audit import log_action
from app.services.csv_import import parse_and_validate_csv

router = APIRouter(prefix="/api/scores", tags=["scores"])

CSV_TEMPLATE = "student_id_number,subject_name,score_type,value,date,notes\nS001,Math,quiz,85,2026-03-01,\n"


@router.get("/template.csv", response_class=PlainTextResponse)
def get_template(_: User = Depends(get_current_user)):
    return PlainTextResponse(
        content=CSV_TEMPLATE,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=scores_template.csv"},
    )


@router.post("", response_model=ScoreResponse, status_code=201)
def create_score(
    body: ScoreCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    score = Score(**body.model_dump())
    db.add(score)
    db.commit()
    db.refresh(score)
    log_action(db, user_id=current_user.id, action="score.create", entity_type="score", entity_id=str(score.id), school_id=current_user.school_id)
    db.commit()
    return score


@router.post("/import", response_model=CSVImportResult)
async def import_scores(
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contents = await file.read()
    result = parse_and_validate_csv(db, contents)
    log_action(db, user_id=current_user.id, action="score.import", entity_type="score", detail=f"{result.imported} rows imported", school_id=current_user.school_id)
    db.commit()
    return result


@router.get("/student/{student_id}", response_model=list[ScoreResponse])
def get_student_scores(
    student_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return db.query(Score).filter(Score.student_id == student_id).order_by(Score.date.desc()).all()
