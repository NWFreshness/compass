import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.db import get_db
from app.middleware.auth import get_current_user, require_role
from app.models import Benchmark, User, UserRole
from app.schemas.benchmark import BenchmarkCreate, BenchmarkResponse, BenchmarkUpdate

router = APIRouter(prefix="/api/benchmarks", tags=["benchmarks"])
benchmark_write_access = Depends(require_role(UserRole.it_admin, UserRole.district_admin))
benchmark_read_access = Depends(require_role(UserRole.it_admin, UserRole.district_admin))


@router.get("", response_model=list[BenchmarkResponse])
def list_benchmarks(
    grade_level: int | None = None,
    subject_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    _: User = benchmark_read_access,
):
    query = db.query(Benchmark)
    if grade_level is not None:
        query = query.filter(Benchmark.grade_level == grade_level)
    if subject_id is not None:
        query = query.filter(Benchmark.subject_id == subject_id)
    return query.order_by(Benchmark.grade_level.asc()).all()


@router.post("", response_model=BenchmarkResponse, status_code=status.HTTP_201_CREATED, dependencies=[benchmark_write_access])
def create_benchmark(body: BenchmarkCreate, db: Session = Depends(get_db)):
    benchmark = Benchmark(**body.model_dump())
    db.add(benchmark)
    db.commit()
    db.refresh(benchmark)
    return benchmark


@router.patch("/{benchmark_id}", response_model=BenchmarkResponse, dependencies=[benchmark_write_access])
def update_benchmark(benchmark_id: uuid.UUID, body: BenchmarkUpdate, db: Session = Depends(get_db)):
    benchmark = db.query(Benchmark).filter(Benchmark.id == benchmark_id).first()
    if not benchmark:
        raise HTTPException(status_code=404, detail="Benchmark not found")

    merged_tier1_min = body.tier1_min if body.tier1_min is not None else benchmark.tier1_min
    merged_tier2_min = body.tier2_min if body.tier2_min is not None else benchmark.tier2_min
    try:
        BenchmarkUpdate(tier1_min=merged_tier1_min, tier2_min=merged_tier2_min)
    except ValidationError as exc:
        errors = []
        for error in exc.errors():
            sanitized_error = dict(error)
            if "ctx" in sanitized_error and "error" in sanitized_error["ctx"]:
                sanitized_error["ctx"] = dict(sanitized_error["ctx"])
                sanitized_error["ctx"]["error"] = str(sanitized_error["ctx"]["error"])
            errors.append(sanitized_error)
        raise HTTPException(status_code=422, detail=errors) from exc

    if body.tier1_min is not None:
        benchmark.tier1_min = body.tier1_min
    if body.tier2_min is not None:
        benchmark.tier2_min = body.tier2_min
    db.commit()
    db.refresh(benchmark)
    return benchmark


@router.delete("/{benchmark_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[benchmark_write_access])
def delete_benchmark(benchmark_id: uuid.UUID, db: Session = Depends(get_db)):
    benchmark = db.query(Benchmark).filter(Benchmark.id == benchmark_id).first()
    if not benchmark:
        raise HTTPException(status_code=404, detail="Benchmark not found")
    db.delete(benchmark)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
