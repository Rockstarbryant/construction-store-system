from fastapi import APIRouter

from app.api.routes import audit_logs, auth, inventory, reports, sites, transactions, users, workers

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(sites.router)
api_router.include_router(workers.router)
api_router.include_router(inventory.router)
api_router.include_router(transactions.router)
api_router.include_router(reports.router)
api_router.include_router(audit_logs.router)
