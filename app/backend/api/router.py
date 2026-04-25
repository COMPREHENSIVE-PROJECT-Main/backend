from fastapi import APIRouter

from app.backend.api.endpoints import auth, cases, report, simulation

router = APIRouter(prefix="/api")

router.include_router(auth.router)
router.include_router(cases.router)
router.include_router(simulation.router)
router.include_router(report.router)