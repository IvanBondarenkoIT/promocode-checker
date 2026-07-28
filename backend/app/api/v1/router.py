from fastapi import APIRouter

from app.api.v1.cashier import router as cashier_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(cashier_router)
