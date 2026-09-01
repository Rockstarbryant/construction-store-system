import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.worker import WorkerCreate, WorkerOut, WorkerSearchResult, WorkerUpdate
from app.services import audit_service, worker_service
from app.utils.formatting import mask_national_id

router = APIRouter(prefix="/workers", tags=["workers"])

_WRITE_ROLES = (UserRole.ADMIN, UserRole.STOREKEEPER)
_READ_ROLES = (UserRole.ADMIN, UserRole.STOREKEEPER, UserRole.MANAGER)


def _to_out(worker) -> WorkerOut:
    return WorkerOut(
        id=worker.id,
        site_id=worker.site_id,
        store_number=worker.store_number,
        full_name=worker.full_name,
        national_id_masked=mask_national_id(worker.national_id),
        phone_number=worker.phone_number,
        department_id=worker.department_id,
        job_role=worker.job_role,
        supervisor=worker.supervisor,
        employment_status=worker.employment_status,
        status=worker.status,
        created_at=worker.created_at,
    )


@router.post("", response_model=WorkerOut, status_code=status.HTTP_201_CREATED)
def register_worker(
    payload: WorkerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*_WRITE_ROLES)),
) -> WorkerOut:
    worker = worker_service.register_worker(db, payload)
    audit_service.record(
        db,
        user_id=current_user.id,
        action="WORKER_REGISTERED",
        entity_type="Worker",
        entity_id=str(worker.id),
        metadata={"store_number": worker.store_number},
    )
    db.commit()
    db.refresh(worker)
    return _to_out(worker)


@router.get("/search", response_model=list[WorkerSearchResult])
def search_workers(
    site_id: uuid.UUID,
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*_READ_ROLES)),
) -> list[WorkerSearchResult]:
    workers = worker_service.search_workers(db, site_id, q)
    return [WorkerSearchResult.model_validate(w) for w in workers]


@router.get("/{worker_id}", response_model=WorkerOut)
def get_worker(
    worker_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*_READ_ROLES)),
) -> WorkerOut:
    worker = worker_service.get_worker(db, worker_id)
    return _to_out(worker)


@router.patch("/{worker_id}", response_model=WorkerOut)
def update_worker(
    worker_id: uuid.UUID,
    payload: WorkerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*_WRITE_ROLES)),
) -> WorkerOut:
    worker = worker_service.update_worker(db, worker_id, payload)
    audit_service.record(
        db,
        user_id=current_user.id,
        action="WORKER_UPDATED",
        entity_type="Worker",
        entity_id=str(worker.id),
        metadata=payload.model_dump(exclude_unset=True),
    )
    db.commit()
    db.refresh(worker)
    return _to_out(worker)
