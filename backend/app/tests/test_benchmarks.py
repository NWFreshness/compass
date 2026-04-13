import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base, Benchmark, School, Subject
from app.schemas.benchmark import BenchmarkCreate, BenchmarkUpdate


def seed_benchmark_world(db):
    school = School(name="Benchmark School")
    subject = Subject(name="Math")
    db.add_all([school, subject])
    db.flush()
    return {"school": school, "subject": subject}


def make_isolated_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    return session, engine


def test_benchmark_create_rejects_invalid_threshold_order():
    with pytest.raises(ValidationError):
        BenchmarkCreate(
            grade_level=4,
            subject_id="11111111-1111-1111-1111-111111111111",
            tier1_min=65,
            tier2_min=70,
        )


def test_benchmark_update_rejects_invalid_threshold_order():
    with pytest.raises(ValidationError):
        BenchmarkUpdate(tier1_min=65, tier2_min=70)


def test_duplicate_grade_and_subject_benchmark_rejected():
    db, engine = make_isolated_session()
    try:
        world = seed_benchmark_world(db)
        benchmark = Benchmark(
            grade_level=4,
            subject_id=world["subject"].id,
            tier1_min=80,
            tier2_min=70,
        )
        db.add(benchmark)
        db.flush()

        duplicate = Benchmark(
            grade_level=4,
            subject_id=world["subject"].id,
            tier1_min=85,
            tier2_min=75,
        )

        with pytest.raises(IntegrityError):
            db.add(duplicate)
            db.flush()
    finally:
        db.close()
        engine.dispose()


def test_invalid_thresholds_are_rejected_by_database_constraints():
    db, engine = make_isolated_session()
    try:
        world = seed_benchmark_world(db)
        benchmark = Benchmark(
            grade_level=4,
            subject_id=world["subject"].id,
            tier1_min=120,
            tier2_min=70,
        )

        with pytest.raises(IntegrityError):
            db.add(benchmark)
            db.flush()
    finally:
        db.close()
        engine.dispose()
