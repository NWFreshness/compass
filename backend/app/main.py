from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from app.routes.ai import router as ai_router
from app.routes.auth import router as auth_router
from app.routes.admin import router as admin_router
from app.routes.lookups import router as lookups_router
from app.routes.students import router as students_router
from app.routes.scores import router as scores_router
from app.routes.dashboard import router as dashboard_router

app = FastAPI(title="Compass API")

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(lookups_router)
app.include_router(students_router)
app.include_router(scores_router)
app.include_router(dashboard_router)
app.include_router(ai_router)


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": "Database integrity error — check for duplicate or invalid references"})
